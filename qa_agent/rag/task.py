"""Document scope and entity clarification; an entity choice never creates SQL.

The registered titles supply document candidates, not database bindings. Only
colliding literal labels need a choice. A wider corpus alone is not ambiguity.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
from uuid import uuid4

from qa_agent.context import current_context


class DocumentTaskError(ValueError):
    pass


def resolve_document_scope(request, settings):
    from qa_agent.documents import load_documents
    documents = load_documents(settings.rag_manifest_path)
    path = settings.rag_index_path / 'index_meta.json'
    metadata = json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {}
    indexed = metadata.get('documents', {})
    if isinstance(indexed, list):
        indexed = {item['doc_id']: item for item in indexed}
    ready = []
    for document in documents:
        item = indexed.get(document['doc_id'], {})
        content_hash = item if isinstance(item, str) else item.get('content_hash')
        if content_hash == document['content_hash']:
            ready.append(document)
    allowed = list(dict.fromkeys(request.scope.doc_ids))
    if allowed:
        selected = [d for d in ready if d['doc_id'] in allowed]
        if len(selected) != len(allowed):
            raise DocumentTaskError('指定文档未登记或索引版本未就绪，未扩大来源范围。')
        return selected
    if not ready:
        raise DocumentTaskError('登记文档尚无可用索引，请先准备资料。')
    return ready


def _labels(document):
    title = str(document.get('title') or '').strip()
    stem = re.sub(r'\s*(?:公开简介|人物简介|简介|介绍|档案|profile|biography)\s*$', '', title, flags=re.I).strip()
    labels = {stem} if len(stem) >= 2 else set()
    # Registration titles can contain both a native name and a translated name.
    labels.update(re.findall(r'[\u3400-\u9fff]{2,}|[A-Za-z][A-Za-z0-9 &.\-]{1,}', stem))
    ref = str(document.get('entity_ref') or '')
    if ref and len(ref.rsplit(':', 1)[-1].strip()) >= 2:
        labels.add(ref.rsplit(':', 1)[-1].strip())
    generic = {'资料', '文档', '手册', '简介', '介绍', '背景', '公开简介',
               '乐队', '乐团', '艺术家', '歌手', '音乐人', '专辑', '曲目',
               '成员', '风格', 'band', 'artist', 'album',
               'profile', 'biography', 'document', 'manual', 'reference'}
    return {label.strip() for label in labels if len(label.strip()) >= 2
            and label.strip().casefold() not in generic}


def document_entity_candidates(question, documents):
    aliases = {}
    for document in documents:
        # Different files alone do not prove different subjects. Without an
        # explicit registration relation, keep ordinary corpus retrieval.
        identity = document.get('entity_ref')
        if not identity:
            continue
        for label in _labels(document):
            aliases.setdefault(label.casefold(), {}).setdefault(identity, []).append(document)
    hits = []
    for label, identities in aliases.items():
        pattern = r'(?<![A-Za-z0-9_])' + re.escape(label) + r'(?![A-Za-z0-9_])'
        for match in re.finditer(pattern, question, re.I):
            hits.append((match.start(), match.end(), label, identities))
    # A unique longer registered name is stronger than a short shared label.
    longest = [hit for hit in hits if not any(other[0] <= hit[0] and other[1] >= hit[1]
        and other[1] - other[0] > hit[1] - hit[0] for other in hits)]
    identities = {}
    for _, _, _, choices in longest:
        for identity, items in choices.items():
            identities.setdefault(identity, {}).update({d['doc_id']: d for d in items})
    if len({(hit[0], hit[1]) for hit in longest}) > 1 and len(identities) != 1:
        # Multiple named subjects stay an ordinary multi-document request;
        # repeating one registered subject does not expand the candidate set.
        return []
    return [{'entity_ref': identity, 'doc_ids': sorted(items),
             'label': ' / '.join(dict.fromkeys(d['title'] for d in items.values())),
             'matched_labels': sorted({hit[2] for hit in longest})}
            for identity, items in sorted(identities.items())]


def ambiguous_document_candidates(question, documents):
    candidates = document_entity_candidates(question, documents)
    return candidates if len(candidates) > 1 else []


def _binding():
    context = current_context()
    return {'context_id': context.context_id, 'version': context.version,
            'content_sha256': context.content_sha256} if context else None


class DocumentTaskStore:
    """Small session-bound, expiring pending cards; no shared protocol changes."""
    def __init__(self, root=None):
        self.root = Path(root) if root else Path(__file__).resolve().parents[2] / '.runtime' / 'document_tasks'

    def path(self, session_id):
        return self.root / (sha256(session_id.encode()).hexdigest() + '.json')

    def discard(self, session_id):
        self.path(session_id).unlink(missing_ok=True)

    def save(self, request, question, candidates):
        card_id = 'doc-' + uuid4().hex
        options = [{'id': 'document-' + str(i + 1), 'label': item['label']}
                   for i, item in enumerate(candidates)]
        payload = {'session_id': request.session_id, 'scope': request.scope.model_dump(mode='json'),
            'context_binding': _binding(), 'original_question': question,
            'reference_datetime': request.reference_datetime, 'timezone': request.timezone,
            'card_id': card_id, 'intent_version': 1, 'candidates': candidates,
            'expires_at': (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()}
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.path(request.session_id)
        temporary = path.with_suffix('.' + uuid4().hex + '.tmp')
        text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        temporary.write_text(json.dumps({'payload': payload, 'sha256': sha256(text.encode()).hexdigest()}, ensure_ascii=False), encoding='utf-8')
        temporary.replace(path)
        return {'clarification_id': card_id, 'intent_version': 1, 'resume_supported': True,
            'level': 'L2', 'reason': '同一称呼对应不同登记对象，需要确认介绍对象。',
            'question': '你要了解哪一个对象？确认后继续回答原问题。', 'options': options}

    def pending(self, request):
        return bool(request.clarification_id and self.path(request.session_id).is_file())

    def resume(self, request, documents):
        path = self.path(request.session_id)
        if not path.is_file():
            raise DocumentTaskError('文档澄清会话不存在，请重新提交完整问题。')
        stored = json.loads(path.read_text(encoding='utf-8'))
        payload = stored['payload']
        text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        if stored.get('sha256') != sha256(text.encode()).hexdigest():
            raise DocumentTaskError('文档澄清状态完整性不符。')
        if (payload['session_id'] != request.session_id or payload['scope'] != request.scope.model_dump(mode='json')
                or payload['context_binding'] != _binding()
                or payload['card_id'] != request.clarification_id or payload['intent_version'] != request.intent_version
                or payload['reference_datetime'] != request.reference_datetime or payload['timezone'] != request.timezone
                or datetime.now(timezone.utc) >= datetime.fromisoformat(payload['expires_at'])):
            raise DocumentTaskError('文档来源、正文或澄清版本已变化，请重新提交完整问题。')
        choices = payload['candidates']
        from qa_agent.intent_consistency import database_operation_request
        trusted_labels = {value for item in choices for value in (item['label'], item['entity_ref'])}
        if request.message.strip() not in trusted_labels and database_operation_request(request.message):
            raise DocumentTaskError('补充内容包含新的数据库任务，请单独提交完整问题，原介绍任务未被覆盖。')
        if request.choice_id:
            match = re.fullmatch(r'document-([1-9][0-9]*)', request.choice_id)
            index = int(match[1]) - 1 if match else -1
            selected = choices[index] if 0 <= index < len(choices) else None
        else:
            matches = [item for item in choices if request.message.strip() in {item['label'], item['entity_ref']}]
            if not matches:
                for item in choices:
                    labels = set().union(*(_labels(d) for d in documents if d['doc_id'] in item['doc_ids']))
                    positive = []
                    for label in labels:
                        for match in re.finditer(r'(?<![A-Za-z0-9_])' + re.escape(label) + r'(?![A-Za-z0-9_])', request.message, re.I):
                            prefix = request.message[max(0, match.start() - 8):match.start()]
                            if not re.search(r'(?:不是|不选|不要)\s*$', prefix):
                                positive.append(label)
                    if positive:
                        matches.append(item)
            selected = matches[0] if len(matches) == 1 else None
        if selected is None:
            raise DocumentTaskError('补充内容没有唯一对应当前文档候选，请选择卡片中的对象。')
        available = {document['doc_id'] for document in documents}
        if not set(selected['doc_ids']) <= available:
            raise DocumentTaskError('原澄清候选已不在有效文档范围内。')
        return payload['original_question'], deepcopy(selected['doc_ids']), {
            'kind': 'document_entity_choice', 'entity_ref': selected['entity_ref'],
            'original_scope': payload['scope'], 'original_question': payload['original_question'],
            'intent_version': payload['intent_version'] + 1, 'changed_fields': ['document_entity'],
            'preserved': ['original_question', 'output_requirements', 'allowed_source_scope'],
            'SQL_binding_or_new_task_created': False}


DEFAULT_DOCUMENT_TASK_STORE = DocumentTaskStore()
