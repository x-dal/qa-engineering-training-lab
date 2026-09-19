import{useState,type FormEvent}from'react';
import{Link,Navigate}from'react-router-dom';
import{api}from'../api/client';
import{Notice}from'../components/Layout';
import{useAuth}from'../context/AuthContext';
import type{User}from'../types';

export default function Register(){
 const{user}=useAuth();
 const[form,setForm]=useState({full_name:'',email:'',password:'',confirm_password:''});
 const[error,setError]=useState(''),[busy,setBusy]=useState(false),[created,setCreated]=useState(false);
 if(user)return <Navigate to="/"/>;
 const set=(key:string,value:string)=>setForm(current=>({...current,[key]:value}));
 async function submit(event:FormEvent){event.preventDefault();setError('');if(form.password!==form.confirm_password){setError('Passwords do not match');return}setBusy(true);try{await api<{access_token:string;user:User}>('/auth/register',{method:'POST',body:JSON.stringify({full_name:form.full_name,email:form.email,password:form.password})});setCreated(true)}catch(reason){setError(reason instanceof Error?reason.message:'Account creation failed')}finally{setBusy(false)}}
 if(created)return <div className="login"><section><div className="brand"><span>OF</span>OrderFlow</div><h1>Account created</h1><Notice type="success" text="Your staff account is ready. You can now sign in."/><Link className="button full" to="/login">Continue to sign in</Link></section></div>;
 return <div className="login"><section><div className="brand"><span>OF</span>OrderFlow</div><h1>Create account</h1><p>New accounts are created with staff access.</p><form onSubmit={submit}><Notice text={error}/><label>Full name<input value={form.full_name} onChange={e=>set('full_name',e.target.value)} minLength={2} required autoComplete="name"/></label><label>Email<input type="email" value={form.email} onChange={e=>set('email',e.target.value)} required autoComplete="email"/></label><label>Password<input type="password" value={form.password} onChange={e=>set('password',e.target.value)} minLength={8} required autoComplete="new-password"/></label><label>Confirm password<input type="password" value={form.confirm_password} onChange={e=>set('confirm_password',e.target.value)} minLength={8} required autoComplete="new-password"/></label><button disabled={busy}>{busy?'Creating…':'Create account'}</button><p className="auth-link">Already registered? <Link to="/login">Sign in</Link></p></form></section></div>
}
