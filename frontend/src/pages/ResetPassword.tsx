import{useState,type FormEvent}from'react';
import{Link}from'react-router-dom';
import{api}from'../api/client';
import{Notice}from'../components/Layout';

export default function ResetPassword(){
 const[form,setForm]=useState({email:'',new_password:'',confirm_password:''});
 const[error,setError]=useState(''),[success,setSuccess]=useState(''),[busy,setBusy]=useState(false);
 const set=(key:string,value:string)=>setForm(current=>({...current,[key]:value}));
 async function submit(event:FormEvent){event.preventDefault();setError('');setSuccess('');if(form.new_password!==form.confirm_password){setError('Passwords do not match');return}setBusy(true);try{const result=await api<{message:string}>('/auth/reset-password',{method:'POST',body:JSON.stringify({email:form.email,new_password:form.new_password})});setSuccess(result.message);setForm({...form,new_password:'',confirm_password:''})}catch(reason){setError(reason instanceof Error?reason.message:'Password reset failed')}finally{setBusy(false)}}
 return <div className="login"><section><div className="brand"><span>OF</span>OrderFlow</div><h1>Reset password</h1><p className="dev-warning"><strong>Development only:</strong> this training flow resets a password without email verification.</p><form onSubmit={submit}><Notice text={error}/><Notice type="success" text={success}/><label>Account email<input type="email" value={form.email} onChange={e=>set('email',e.target.value)} required autoComplete="email"/></label><label>New password<input type="password" value={form.new_password} onChange={e=>set('new_password',e.target.value)} minLength={8} required autoComplete="new-password"/></label><label>Confirm new password<input type="password" value={form.confirm_password} onChange={e=>set('confirm_password',e.target.value)} minLength={8} required autoComplete="new-password"/></label><button disabled={busy}>{busy?'Resetting…':'Reset password'}</button><p className="auth-link"><Link to="/login">Back to sign in</Link></p></form></section></div>
}
