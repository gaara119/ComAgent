"""Capture real D3 clarification UI/API before/after and two metric switches."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
import time
from uuid import uuid4

import httpx
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.capture_d2_demo import wait_api_record, session_post_count, safe_text, capture_records


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--api-records',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--ui-url',default='http://127.0.0.1:8501')
    parser.add_argument('--api-url',default='http://127.0.0.1:8000')
    parser.add_argument('--browser-path',type=Path,default=Path(r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'))
    args=parser.parse_args()
    args.api_records=(ROOT/args.api_records).resolve() if not args.api_records.is_absolute() else args.api_records.resolve()
    output=args.output if args.output.is_absolute() else ROOT/args.output
    if output.exists():raise SystemExit('Output exists; preserve older actual screenshot runs.')
    output.mkdir(parents=True)
    screenshot_root=ROOT/'notes/screenshots'
    screenshot_root.mkdir(parents=True,exist_ok=True)
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    report={'created_at_utc':datetime.now(timezone.utc).isoformat(),'command':[sys.executable,'-B',*sys.argv],
            'method':'Real Edge + Streamlit + existing project actual API capture middleware',
            'holdout_predictions':0,'status':'RUNNING','checks':[],'screenshots':[],'errors':[]}
    def save():
        (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    def check(name,condition,details=None):
        report['checks'].append({'name':name,'passed':bool(condition),'actual':details})
    def wait_next_record(session_id, prior_trace):
        deadline=time.monotonic()+240
        while time.monotonic()<deadline:
            rows=[record for _,record in capture_records(args.api_records) if record['request']['session_id']==session_id and record['response']['trace_id']!=prior_trace]
            if rows:
                # A switch may already have an older request in this session;
                # choose the greatest current intent version then trace identity.
                newest=max(rows,key=lambda record:(record['response'].get('intent') or {}).get('intent_version',0))
                if (newest['response'].get('intent') or {}).get('intent_version',0)>(prior_versions.get(prior_trace,0)):
                    return newest
            time.sleep(.2)
        raise RuntimeError('No actual new API response after this UI action.')
    prior_versions={}
    def capture(page,name,expected_trace=None):
        caption=(page.get_by_text('请求编号：'+expected_trace,exact=True) if expected_trace else
                 page.get_by_text('请求编号：',exact=False))
        # Streamlit can preserve an expander's open state across a rerun.
        # Await this exact response in the DOM before toggling it, and expand
        # only when needed; blindly clicking may close the new response.
        caption.wait_for(state='attached',timeout=30000)
        if not caption.is_visible():
            page.get_by_text('处理步骤与耗时',exact=True).click()
        caption.wait_for(timeout=30000)
        trace_id=caption.inner_text().split('：',1)[-1].strip()
        path,record=wait_api_record(args.api_records,trace_id)
        prior_versions[trace_id]=(record['response'].get('intent') or {}).get('intent_version',0)
        (output/(name+'-raw.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
        image=screenshot_root/f'D3-{run_id}-{name}.png'
        page.screenshot(path=str(image),full_page=True)
        report['screenshots'].append({'file':image.relative_to(ROOT).as_posix(),'trace_id':trace_id,
                                      'raw':(output/(name+'-raw.json')).relative_to(ROOT).as_posix(),
                                      'actual_api_record':path.relative_to(ROOT).as_posix()})
        page.get_by_text('处理步骤与耗时',exact=True).click()
        save()
        return record
    def submit(page,question):
        page.goto(args.ui_url,wait_until='networkidle')
        box=page.get_by_role('textbox',name='你的问题');box.wait_for(timeout=60000)
        box.fill(question);box.press('Tab')
        page.get_by_role('button',name='提交问题',exact=True).click()
    with httpx.Client(timeout=20,trust_env=False) as client:
        health=client.get(args.api_url+'/health').json()
        if health.get('stage')!='D3':raise SystemExit('D3 API not active: no UI model queries started.')
    save()
    with sync_playwright() as playwright:
        options={'headless':True}
        if args.browser_path.is_file():options['executable_path']=str(args.browser_path)
        browser=playwright.chromium.launch(**options)
        try:
            page=browser.new_page(viewport={'width':1440,'height':1800})
            submit(page,'账单国家为USA的发票销售额同比增长多少？')
            page.get_by_test_id('stAlert').filter(has_text='需要补充信息').wait_for(timeout=240000)
            before=capture(page,'clarification-before')
            check('l2_no_sql_execution',before['response']['status']=='NEEDS_CLARIFICATION' and before['response'].get('sql') is None)
            session=before['request']['session_id']
            prior_count=session_post_count(args.api_records,session)
            page.get_by_role('button',name=re.compile(r'^2024年')).click()
            page.get_by_test_id('stAlert').filter(has_text='回答完成').wait_for(timeout=240000)
            new=wait_next_record(session,before['response']['trace_id'])
            after=capture(page,'clarification-after',new['response']['trace_id'])
            check('same_session_and_version',after['request']['session_id']==session and after['request'].get('intent_version')==before['response']['clarification']['intent_version'])
            check('one_button_one_request',session_post_count(args.api_records,session)==prior_count+1)
            check('resumed_actual_sql',after['response']['status']=='SUCCEEDED' and bool(after['response'].get('sql')))
            page.close()
            page=browser.new_page(viewport={'width':1440,'height':1800})
            submit(page,'按账单国家统计USA的发票总额同比增长率是多少？')
            page.get_by_role('textbox',name='补充说明',exact=True).wait_for(timeout=240000)
            free_before=capture(page,'free-input-before')
            free_session=free_before['request']['session_id']
            prior_count=session_post_count(args.api_records,free_session)
            page.get_by_role('textbox',name='补充说明',exact=True).fill('2024年')
            page.get_by_role('button',name='提交补充',exact=True).click()
            page.get_by_test_id('stAlert').filter(has_text='回答完成').wait_for(timeout=240000)
            new=wait_next_record(free_session,free_before['response']['trace_id'])
            free_after=capture(page,'free-input-after',new['response']['trace_id'])
            current=((free_after['response'].get('intent') or {}).get('time_scope') or {}).get('current') or {}
            check('free_input_actual_resume',free_after['request']['message']=='2024年' and
                  not free_after['request'].get('choice_id') and free_after['response']['status']=='SUCCEEDED' and
                  current.get('start')=='2024-01-01',free_after['response']['trace_id'])
            check('one_free_submit_one_request',session_post_count(args.api_records,free_session)==prior_count+1)
            page.close()
            page=browser.new_page(viewport={'width':1440,'height':1800})
            submit(page,'2024年最受欢迎的5首曲目是哪些？')
            page.get_by_role('button',name='切换：按销售额',exact=True).wait_for(timeout=240000)
            default=capture(page,'popular-default')
            check('l1_assumption_visible',default['response']['metadata']['clarify']['level']=='L1' and bool(default['response']['metadata']['clarify']['assumptions']))
            page.get_by_role('button',name='切换：按销售额',exact=True).click()
            page.get_by_text('用户已选择热门曲目口径：按销售额。',exact=False).wait_for(timeout=240000)
            new=wait_next_record(default['request']['session_id'],default['response']['trace_id'])
            revenue=capture(page,'switch-revenue',new['response']['trace_id'])
            check('switch_new_version',revenue['response']['intent']['intent_version']>default['response']['intent']['intent_version'])
            page.get_by_role('button',name='切换：按购买数量',exact=True).click()
            page.get_by_text('用户已选择热门曲目口径：按购买数量。',exact=False).wait_for(timeout=240000)
            new=wait_next_record(revenue['request']['session_id'],revenue['response']['trace_id'])
            quantity=capture(page,'switch-back-quantity',new['response']['trace_id'])
            check('switch_back_new_card',quantity['request']['clarification_id']!=revenue['request']['clarification_id'] and quantity['response']['metadata']['clarify']['level']=='L0')
            check('three_panels_preserved',page.get_by_test_id('stExpander').count()==3)
        except Exception as exc:
            report['errors'].append(safe_text(exc))
            report['status']='FAILED';save();raise
        finally:browser.close()
    report['status']='PASS' if all(row['passed'] for row in report['checks']) else 'FAIL'
    save();print(json.dumps({'status':report['status'],'checks':len(report['checks']),'screenshots':len(report['screenshots'])},ensure_ascii=False))


if __name__=='__main__':main()
