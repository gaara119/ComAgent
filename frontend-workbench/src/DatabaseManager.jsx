import React, { useEffect, useRef, useState } from 'react';
import { Alert, Button, Empty, Form, Input, InputNumber, Modal, Popconfirm, Select, Space, Table, Tag, message } from 'antd';
import { publicDatabase, safeText, databaseErrorMessage } from './contract.mjs';

const initialValues={port:5432,sslmode:'prefer',schemas:'public'};
const endpoint=id=>`/api/databases/${encodeURIComponent(id)}`;

/** Only the in-memory form holds the password; every close and successful add clears it. */
export default function DatabaseManager({open,onClose,request,databases,listError,onAdded,onRefreshList,onRemoved,disabled=false}) {
  const [form]=Form.useForm();
  const [action,setAction]=useState(''),[error,setError]=useState(''),[selected,setSelected]=useState('');
  const actionLock=useRef(false);
  const wasOpened=useRef(false);
  useEffect(()=>{if(open){wasOpened.current=true;}else if(wasOpened.current){form.setFieldValue('password','');setError('');}},[open,form]);
  const active=databases.find(item=>item.db_id===selected);
  const summary=active?.catalog_summary;
  function close(){if(actionLock.current)return;form.setFieldValue('password','');setError('');onClose();}
  async function add(values){
    if(actionLock.current||disabled)return;
    actionLock.current=true;setAction('add');setError('');
    try {
      const payload={...values,password:values.password||'',port:Number(values.port),schemas:String(values.schemas||'').split(',').map(value=>value.trim()).filter(Boolean)};
      const saved=publicDatabase(await request('/api/databases',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}));
      if(!saved)throw new Error('服务没有返回有效的数据库连接编号。');
      form.setFieldValue('password','');
      await onAdded(saved);
      form.resetFields();message.success(`已连接 ${saved.label}，可以开始提问。`);onClose();
    } catch(exc) {
      // Even an upstream error that echoes the submitted password cannot display it.
      setError(databaseErrorMessage(exc,values.password||''));
    } finally {actionLock.current=false;setAction('');}
  }
  async function refreshDatabase(item){
    if(actionLock.current||disabled)return;
    actionLock.current=true;setAction(`refresh:${item.db_id}`);setError('');
    try{await request(`${endpoint(item.db_id)}/refresh`,{method:'POST'});await onRefreshList();setSelected(item.db_id);message.success('连接与库结构已刷新。');}
    catch(exc){setError(safeText(exc.message));}
    finally{actionLock.current=false;setAction('');}
  }
  async function remove(item){
    if(actionLock.current||disabled)return;
    actionLock.current=true;setAction(`remove:${item.db_id}`);setError('');
    try{await request(endpoint(item.db_id),{method:'DELETE'});await onRemoved(item.db_id);if(selected===item.db_id)setSelected('');message.success('已移除本地连接，源数据库没有改变。');}
    catch(exc){setError(safeText(exc.message));}
    finally{actionLock.current=false;setAction('');}
  }
  return <Modal title="添加与管理数据库" open={open} onCancel={close} footer={null} width={900} className="database-modal" destroyOnHidden closable={!action} maskClosable={!action} keyboard={!action}>
    <p className="database-intro">连接 PostgreSQL，验证只读访问并读取库结构。连接成功后会切换到新数据库，开始一个新的问答会话。</p>
    {listError&&<Alert className="database-error" type="warning" showIcon title="无法加载数据库列表" description={listError}/>}
    {error&&<Alert className="database-error" type="error" showIcon title="操作未完成" description={error}/>}
    <Form form={form} name="add-database" layout="vertical" initialValues={initialValues} onFinish={add} preserve={false} disabled={Boolean(action)||disabled} requiredMark={false} autoComplete="off">
      <div className="database-form-grid">
        <Form.Item className="database-full" label="连接名称" name="name" rules={[{required:true,whitespace:true,message:'请输入连接名称。'},{max:80,message:'连接名称不能超过80个字符。'}]}><Input placeholder="例如：业务分析库" maxLength={80}/></Form.Item>
        <Form.Item label="主机地址" name="host" rules={[{required:true,whitespace:true,message:'请输入 PostgreSQL 主机地址。'}]}><Input placeholder="localhost 或数据库主机名" autoComplete="off"/></Form.Item>
        <Form.Item label="端口" name="port" rules={[{required:true,message:'请输入端口。'}]}><InputNumber min={1} max={65535} style={{width:'100%'}}/></Form.Item>
        <Form.Item label="数据库名称" name="database" rules={[{required:true,whitespace:true,message:'请输入数据库名称。'}]}><Input placeholder="数据库名称" autoComplete="off"/></Form.Item>
        <Form.Item label="用户名" name="user" rules={[{required:true,whitespace:true,message:'请输入用户名。'}]}><Input placeholder="建议使用只读账号" autoComplete="off"/></Form.Item>
        <Form.Item label="密码" name="password"><Input.Password autoComplete="new-password" placeholder="连接密码（允许留空）" maxLength={4096} visibilityToggle={false}/></Form.Item>
        <Form.Item label="SSL 模式" name="sslmode"><Select options={['prefer','require','verify-ca','verify-full','disable','allow'].map(value=>({value,label:value}))}/></Form.Item>
        <Form.Item className="database-full" label="Schema 范围" name="schemas" rules={[{required:true,whitespace:true,message:'请填写至少一个 schema。'}]} extra="多个 schema 用英文逗号分隔。"><Input placeholder="public, analytics"/></Form.Item>
      </div>
      <div className="database-form-footer"><p className="subtle">密码仅用于连接，不会写入浏览器本地存储、会话记录或导出结果。关闭窗口后会清空密码。</p><Button type="primary" htmlType="submit" loading={action==='add'} disabled={Boolean(action)||disabled}>验证并添加数据库</Button></div>
    </Form>
    <section className="database-connections"><div className="database-section-heading"><h3>已登记的数据库</h3><Button size="small" onClick={onRefreshList} disabled={Boolean(action)||disabled}>重新加载列表</Button></div>
      {databases.length?<Table size="small" rowKey="db_id" pagination={false} dataSource={databases} scroll={{x:590}} columns={[
        {title:'连接',dataIndex:'label',render:(label,item)=><><strong>{label}</strong><div className="subtle">{item.builtin?'内置目录由项目维护':'本地登记连接'}</div></>},
        {title:'库结构',render:(_,item)=><Tag color={item.configured&&item.catalog_exists?'success':'warning'}>{item.catalog_exists?`${item.catalog_summary?.table_count??'—'} 张表`:'尚未就绪'}</Tag>},
        {title:'操作',render:(_,item)=><Space wrap size="small"><Button size="small" disabled={Boolean(action)||disabled} onClick={()=>setSelected(item.db_id)}>结构摘要</Button>{!item.builtin&&<><Button size="small" loading={action===`refresh:${item.db_id}`} disabled={Boolean(action)||disabled} onClick={()=>refreshDatabase(item)}>刷新结构</Button><Popconfirm title="移除此本地连接？" description="只移除本项目登记的连接，不会删除源数据库。" onConfirm={()=>remove(item)} okText="移除连接" cancelText="取消"><Button size="small" danger disabled={Boolean(action)||disabled} loading={action===`remove:${item.db_id}`}>移除</Button></Popconfirm></>}</Space>}
      ]}/>:<Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="尚无可用数据库连接"/>}
      {active&&<div className="database-summary"><h3>{active.label} · 库结构摘要</h3><p className="subtle">{summary?.table_count??'—'} 张表 · {summary?.column_count??'—'} 个字段 · {summary?.foreign_key_count??'—'} 条外键{summary?.schemas?.length?` · ${summary.schemas.join('、')}`:''}</p>{summary?.tables?.length>0?<div className="database-table-tags">{summary.tables.map(item=><Tag key={`${item.schema}.${item.name}`}>{item.schema}.{item.name} · {item.column_count} 字段</Tag>)}</div>:<p className="subtle">当前没有可显示的表结构，请刷新结构或检查连接。</p>}</div>}
    </section>
  </Modal>;
}
