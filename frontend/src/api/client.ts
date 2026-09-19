const API_URL=import.meta.env.VITE_API_URL||'http://localhost:8000/api/v1';
export class ApiError extends Error{constructor(public status:number,message:string,public details?:unknown){super(message)}}
export async function api<T>(path:string,options:RequestInit={}):Promise<T>{
 const token=localStorage.getItem('orderflow_token'); const headers=new Headers(options.headers); headers.set('Content-Type','application/json'); if(token)headers.set('Authorization',`Bearer ${token}`);
 const response=await fetch(`${API_URL}${path}`,{...options,headers}); if(response.status===204)return undefined as T;
 const data=await response.json().catch(()=>({})); if(!response.ok){const detail=data.detail||data.error?.message||'Request failed';throw new ApiError(response.status,typeof detail==='string'?detail:'Request validation failed',data.error?.details)} return data as T;
}
export const qs=(values:Record<string,string|number|boolean|undefined>)=>'?'+new URLSearchParams(Object.entries(values).filter(([,v])=>v!==undefined&&v!=='').map(([k,v])=>[k,String(v)])).toString();
