"use client";
import {useMemo,useState} from 'react';
import {Plus} from 'lucide-react';
import {Combobox,ComboboxInput,ComboboxContent,ComboboxList,ComboboxItem,ComboboxEmpty} from '@/components/ui/combobox';
import {Select,SelectTrigger,SelectValue,SelectContent,SelectItem} from '@/components/ui/select';
import type {Champion} from '@/lib/draft';
export function Portrait({champion,size='normal'}:{champion?:Champion;size?:string}){
 return <span className={'portrait '+size}>{champion?<img src={champion.image} alt={champion.zh} loading="lazy"/>:<Plus size={18}/>}</span>;
}
export function ChampionPicker({champions,value,onChange,disabledIds=[],label='搜索英雄',placeholder='中文 / English / 简称'}:{champions:Champion[];value:string|null;onChange:(id:string|null)=>void;disabledIds?:string[];label?:string;placeholder?:string}){
 const [query,setQuery]=useState('');
 const selected=champions.find(c=>c.id===value)??null;
 const items=useMemo(()=>champions.filter(c=>!disabledIds.includes(c.id)||c.id===value).filter(c=>`${c.zh} ${c.name} ${c.id} ${c.title} ${c.aliases}`.toLowerCase().includes(query.toLowerCase())),[champions,disabledIds,query,value]);
 return <Combobox items={items} value={selected} onValueChange={(c:Champion|null)=>{onChange(c?.id??null);setQuery('');}} onInputValueChange={setQuery} filter={null} itemToStringLabel={(c:Champion)=>c.zh}><ComboboxInput aria-label={label} placeholder={placeholder} showClear={!!value} className="champion-input"/><ComboboxContent className="champion-popup"><ComboboxEmpty>没有匹配的可选英雄</ComboboxEmpty><ComboboxList>{(c:Champion)=><ComboboxItem key={c.id} value={c} className="champion-option"><Portrait champion={c} size="small"/><span><b>{c.zh}</b><small>{c.name}</small></span></ComboboxItem>}</ComboboxList></ComboboxContent></Combobox>;
}
export function Choice({value,onChange,items,label,className=''}:{value:string;onChange:(v:string)=>void;items:{value:string;label:string}[];label:string;className?:string}){
 return <Select value={value} onValueChange={onChange}><SelectTrigger aria-label={label} className={className}><SelectValue/></SelectTrigger><SelectContent>{items.map(i=><SelectItem key={i.value} value={i.value}>{i.label}</SelectItem>)}</SelectContent></Select>;
}
