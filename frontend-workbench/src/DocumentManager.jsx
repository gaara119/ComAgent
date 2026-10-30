import React, { useRef, useState } from 'react';
import { Alert, Button, Form, Input, Modal, Radio, Space, Tabs, message } from 'antd';

const ACCEPT='.pdf,.docx,.txt,.md,.markdown';
const LIMIT=8*1024*1024;
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
function encodeFile(file){
  return new Promise((resolve,reject)=>{
    const reader=new FileReader();
    reader.onerror=()=>reject(new Error('文件读取失败，请重新选择。'));
    reader.onload=()=>resolve(String(reader.result).split(',')[1]);
    reader.readAsDataURL(file);
  });
}

/** One text entry supports persistent knowledge and session-only context. */
export default function DocumentManager({open,mode='file',textTarget='knowledge',sessionText='',onClose,request,onAdded,onSaveSession,onBusyChange}){
  const [form]=Form.useForm();
  const [file,setFile]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState(''),[progress,setProgress]=useState('');
  const lock=useRef(false);
  const [tab,setTab]=useState(mode);
  const [target,setTarget]=useState(textTarget);
  const sessionOnly=tab==='text'&&target==='session';
  React.useEffect(()=>{if(open){setTab(mode);setTarget(textTarget);setError('');setProgress('');if(mode==='text'&&textTarget==='session')form.setFieldValue('text',sessionText);}},[open,mode,textTarget,form]);
  function close(){if(lock.current)return;form.resetFields();setFile(null);setError('');setProgress('');onClose();}
  function selectFile(event){
    const next=event.target.files?.[0]||null;setError('');
    if(next&&(!/\.(pdf|docx|txt|md|markdown)$/i.test(next.name)||next.size>LIMIT||next.size===0)){
      setFile(null);event.target.value='';setError('请选择不超过 8 MB 的 PDF、DOCX、TXT 或 Markdown 文件。');return;
    }
    setFile(next);if(next&&!form.getFieldValue('title'))form.setFieldValue('title',next.name.replace(/\.[^.]+$/,''));
  }
  async function save(values){
    if(lock.current)return;
    if(tab==='file'&&!file){setError('请先选择需要上传的文件。');return;}
    lock.current=true;setBusy(true);onBusyChange(true);setError('');setProgress('正在提交资料……');
    try{
      if(sessionOnly){
        setProgress('正在保存本次会话文字……');
        await onSaveSession(values.text);
        message.success('文字已保存到当前会话，可以继续提问。');
        form.resetFields();onClose();return;
      }
      const title=values.title.trim();
      const payload=tab==='file'?{title,filename:file.name,content_base64:await encodeFile(file)}:{title,text:values.text};
      let job=await request(`/api/documents/${tab==='file'?'import':'text'}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
      const id=job.job_id;
      if(!/^[a-f0-9]{32}$/.test(id||''))throw new Error('服务未返回有效的导入任务编号。');
      const deadline=Date.now()+10*60*1000;
      while(['queued','indexing'].includes(job.status)){
        setProgress(job.message||'正在建立检索索引……');
        if(Date.now()>deadline)throw new Error(`等待导入超时，后台任务可能仍在运行。请稍后刷新文档列表，避免重复上传。任务：${id}`);
        await delay(1500);job=await request(`/api/documents/imports/${id}`);
      }
      if(job.status!=='ready'||!job.document?.ready)throw new Error(job.message||'资料未确认导入成功。');
      await onAdded(job.document);
      message.success('资料已建立索引，已切换到该文档，可以直接提问。');
      form.resetFields();setFile(null);onClose();
    }catch(exc){setError(exc.message);}
    finally{setProgress('');lock.current=false;setBusy(false);onBusyChange(false);}
  }
  return <Modal className="document-modal" title="添加文档与文字" open={open} onCancel={close} footer={null} width={760} destroyOnHidden closable={!busy} maskClosable={!busy} keyboard={!busy}>
    <p className="subtle">上传文档会保存到本地知识库。添加文字时，可以选择长期保存或仅用于本次会话。</p>
    <Tabs activeKey={tab} onChange={value=>{if(!busy){setTab(value);setError('');}}} items={[{key:'file',label:'上传文档',disabled:busy},{key:'text',label:'添加文字',disabled:busy}]}/>
    {error&&<Alert type="error" showIcon title="未完成导入" description={error} style={{marginBottom:16}}/>}
    {progress&&<Alert type="info" showIcon title={progress} style={{marginBottom:16}}/>}
    <Form form={form} layout="vertical" onFinish={save} disabled={busy} requiredMark={false}>
      {tab==='text'&&<Form.Item label="保存范围"><Radio.Group aria-label="文字保存范围" value={target} disabled={busy} onChange={event=>{setTarget(event.target.value);setError('');if(event.target.value==='session'&&!form.getFieldValue('text'))form.setFieldValue('text',sessionText);}} options={[{value:'knowledge',label:'知识库（长期保存）'},{value:'session',label:'仅本次会话'}]}/><p className="subtle">{sessionOnly?'文字仅绑定当前会话。切换来源或新建会话后需重新添加；替换文字会清空当前显示的问答记录。':'建立检索索引后，后续会话仍可选择这份资料。'}</p></Form.Item>}
      {!sessionOnly&&<Form.Item name="title" label="资料标题" rules={[{required:true,whitespace:true,message:'请填写资料标题。'},{max:200,message:'标题最多200个字符。'}]}><Input aria-label="资料标题" maxLength={200} placeholder="例如：项目介绍、业务指标说明"/></Form.Item>}
      {tab==='file'?<div className="document-upload-field"><label htmlFor="source-document-file">选择文档</label><input key={open?'open':'closed'} id="source-document-file" aria-label="选择文档文件" type="file" accept={ACCEPT} disabled={busy} onChange={selectFile}/><p className="subtle">PDF / Word（.docx）/ TXT / Markdown，单个文件最多 8 MB；PDF 最多 100 页。TXT 和 Markdown 使用 UTF-8 编码。</p>{file&&<p>{file.name} · {(file.size/1024).toFixed(1)} KB</p>}</div>:
        <Form.Item name="text" label="资料正文" rules={[{required:true,whitespace:true,message:'请填写资料正文。'},{max:120000,message:'正文最多120000个字符。'}]}><Input.TextArea aria-label={sessionOnly?'本次会话资料正文':'知识库资料正文'} autoSize={{minRows:10,maxRows:18}} maxLength={120000} showCount placeholder={sessionOnly?'粘贴仅供本次会话参考的背景、名单或完整正文……':'粘贴需要长期保留和检索的文字资料……'}/></Form.Item>}
      <Space style={{marginTop:20}}><Button type="primary" htmlType="submit" loading={busy}>{sessionOnly?'保存到本次会话':'保存并建立索引'}</Button><Button disabled={busy} onClick={close}>取消</Button></Space>
    </Form>
  </Modal>;
}
