export type Role='TOP'|'JUNGLE'|'MIDDLE'|'BOTTOM'|'UTILITY';
export type Champion={id:string;name:string;zh:string;title:string;image:string;roles:Role[];aliases:string;traits:string[]};
export type Pick={champion_id:string|null;role:Role|null;status:'locked'|'hover'};
export type Draft={role:Role;allies:Pick[];enemies:Pick[];bans:string[];pool_only:boolean;queue:420|440};
export type Pool={champion_id:string;role:Role;comfort:number};
export type Stat={champion_id:string;role:Role;games:number;wins:number};
export type Profile={pool:Pool[];statistics:Stat[];account:{game_name?:string;tag_line?:string;synced_at?:number}};
export type Status={vision_ready:boolean;riot_ready:boolean;patch:string};
export type Recommendation={champion:Champion;score:number;components:Record<string,number>;reasons:string[];risks:string[];games:number;wins:number;win_rate:number|null;comfort:number|null};
export type Result={recommendations:Recommendation[];candidates:number;uncertain:boolean;note:string};
export type VisionSlot={side:'left'|'right'|'unknown';slot:number;champion_id:string|null;state:'champion'|'empty'|'uncertain'};
export type Job={id:string;status:'running'|'done'|'error';completed:number;total:number;message:string};
export const ROLES:Role[]=['TOP','JUNGLE','MIDDLE','BOTTOM','UTILITY'];
export const LABELS:Record<Role,string>={TOP:'上单',JUNGLE:'打野',MIDDLE:'中单',BOTTOM:'下路',UTILITY:'辅助'};
export const fresh=():Draft=>({role:'UTILITY',allies:ROLES.map(role=>({role,champion_id:null,status:'locked'})),enemies:ROLES.map(()=>({role:null,champion_id:null,status:'locked'})),bans:[],pool_only:false,queue:420});
export async function api<T>(path:string,options:RequestInit={}):Promise<T>{
 const response=await fetch('/api'+path,{...options,headers:options.body instanceof FormData?undefined:{'Content-Type':'application/json',...options.headers}});
 const data=await response.json().catch(()=>({detail:'服务响应异常，请确认应用已启动'}));
 if(!response.ok){const detail=typeof data.detail==='string'?data.detail:Array.isArray(data.detail)?data.detail.map((x:{msg:string})=>x.msg).join('；'):'请求失败';throw new Error(detail);}return data;
}
export const errorText=(e:unknown)=>e instanceof Error?e.message:'连接失败，请重试';
