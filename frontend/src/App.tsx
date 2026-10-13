import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";

type View = "public" | "internal";
type Concept = { code: string; name: string; group: string; display_order: number };
type Channel = { id: number; name: string };
type Load = { id:number; revenue_date:string; tgp_entry_date:string; channel:string; status:string; uploaded_at:string; gross_total:string; commission_total:string; vat_total:string; net_total:string; receipt_count:number; source_name:string };
type Counter = { gross_visible:string; revenue_date:string|null; updated_at:string; is_progressing:boolean; load_count:number; refresh_seconds:number; animation_seconds:number; animation_style?:string; adaptive_animation?:boolean; counter_gross_only:boolean; show_group_breakdown:boolean; display_period?:string; period_label?:string; reference_date?:string; groups?:Record<string,string> };
type ConfigForm = { algorithm:string; publication_delay_minutes:string; interval_value:string; interval_unit:string; display_period:string; reference_date:string; max_variation_percent:string; randomness_intensity_percent:string; smoothing_intervals:string; tv_animation_seconds:string; animation_style:string; adaptive_animation:boolean; gamma:string; counter_gross_only:boolean; show_group_breakdown:boolean };
type AuthUser = { id:number; username:string; email:string; first_name:string; last_name:string; full_name:string; is_active:boolean; is_superuser:boolean; roles:string[]; permissions:string[]; last_login:string|null };
type ManagedUser = AuthUser;

const money = new Intl.NumberFormat("es-AR", { style:"currency", currency:"ARS", minimumFractionDigits:2 });
const today = new Date().toISOString().slice(0, 10);
const animationNames:Record<string,string>={INCREMENTAL:"Contador incremental",ODOMETER:"Odómetro",COMBINED:"Combinado",FLIP:"Flip institucional",SLIDE:"Deslizamiento suave",PULSE:"Pulso luminoso",ROLLING:"Rodillo simultáneo",FLUID:"Conteo fluido"};

function cookie(name:string){return document.cookie.split(";").map((item)=>item.trim()).find((item)=>item.startsWith(`${name}=`))?.slice(name.length+1)||"";}
function secureHeaders(headers:HeadersInit={}){return {...headers,"X-CSRFToken":decodeURIComponent(cookie("csrftoken"))};}

type ApiPayload={error?:string;detail?:string;[key:string]:unknown};
async function readApiResponse(response:Response,fallback:string):Promise<ApiPayload>{
  const contentType=response.headers.get("content-type")||"";
  if(!contentType.toLowerCase().includes("application/json")){
    await response.text().catch(()=>"");
    throw new Error(response.status===404?"El servicio de recuperación no está disponible en este momento. Recargá la página e intentá nuevamente.":fallback);
  }
  const result=await response.json() as ApiPayload;
  if(!response.ok)throw new Error(typeof result.error==="string"?result.error:fallback);
  return result;
}

function LoginScreen({onLogin,onPublic}:{onLogin:(user:AuthUser)=>void;onPublic:()=>void}){
  const resetParams=location.hash.startsWith("#restablecer?")?new URLSearchParams(location.hash.split("?",2)[1]):null;
  const [mode,setMode]=useState<"login"|"request"|"reset">(resetParams?"reset":"login");
  const [username,setUsername]=useState("");const [password,setPassword]=useState("");const [passwordConfirmation,setPasswordConfirmation]=useState("");const [firstName,setFirstName]=useState("");const [lastName,setLastName]=useState("");const [email,setEmail]=useState("");const [bootstrap,setBootstrap]=useState<{required:boolean;available:boolean}|null>(null);const [busy,setBusy]=useState(false);const [error,setError]=useState("");const [message,setMessage]=useState("");
  useEffect(()=>{fetch("/api/auth/bootstrap/status/").then((response)=>response.json()).then(setBootstrap).catch(()=>setBootstrap({required:false,available:false}));},[]);
  async function submit(event:FormEvent){event.preventDefault();setBusy(true);setError("");try{await fetch("/api/auth/csrf/");const initial=Boolean(bootstrap?.required&&bootstrap.available);const response=await fetch(initial?"/api/auth/bootstrap/":"/api/auth/login/",{method:"POST",headers:secureHeaders({"Content-Type":"application/json"}),body:JSON.stringify(initial?{username,password,first_name:firstName,last_name:lastName,email}:{username,password})});const result=await response.json();if(!response.ok)throw new Error(result.error||"No fue posible iniciar sesión");onLogin(result);}catch(reason){setError(reason instanceof Error?reason.message:"No fue posible iniciar sesión");}finally{setBusy(false);}}
  async function requestReset(event:FormEvent){event.preventDefault();setBusy(true);setError("");setMessage("");try{await fetch("/api/auth/csrf/");const response=await fetch("/api/auth/password-reset/",{method:"POST",headers:secureHeaders({"Content-Type":"application/json"}),body:JSON.stringify({email})});const result=await readApiResponse(response,"No fue posible solicitar el cambio");setMessage(typeof result.detail==="string"?result.detail:"Si el correo está registrado, recibirás un enlace para restablecer la contraseña.");}catch(reason){setError(reason instanceof Error?reason.message:"No fue posible solicitar el cambio");}finally{setBusy(false);}}
  async function confirmReset(event:FormEvent){event.preventDefault();setError("");setMessage("");if(password!==passwordConfirmation){setError("Las contraseñas no coinciden");return;}setBusy(true);try{await fetch("/api/auth/csrf/");const response=await fetch("/api/auth/password-reset/confirm/",{method:"POST",headers:secureHeaders({"Content-Type":"application/json"}),body:JSON.stringify({uid:resetParams?.get("uid")||"",token:resetParams?.get("token")||"",password})});const result=await readApiResponse(response,"No fue posible cambiar la contraseña");history.replaceState(null,"",`${location.pathname}${location.search}`);setPassword("");setPasswordConfirmation("");setMode("login");setMessage(typeof result.detail==="string"?result.detail:"La contraseña fue actualizada correctamente.");}catch(reason){setError(reason instanceof Error?reason.message:"No fue posible cambiar la contraseña");}finally{setBusy(false);}}
  const initial=Boolean(bootstrap?.required&&bootstrap.available);
  if(mode==="request")return <main className="login-screen"><form className="login-card" onSubmit={requestReset}><img src="/brand/arcat.png" alt="ARCAT · Agencia de Recaudación Catamarca"/><p>Recuperar contraseña</p><label>Correo electrónico<input autoFocus type="email" autoComplete="email" required value={email} onChange={(e)=>setEmail(e.target.value)}/></label>{message&&<div className="notice notice--ok">{message}</div>}{error&&<div className="notice notice--error">{error}</div>}<button className="primary" disabled={busy}>{busy?"Enviando…":"Enviar enlace"}</button><button type="button" className="login-public" onClick={()=>{setMode("login");setError("");setMessage("");}}>Volver al ingreso</button></form></main>;
  if(mode==="reset")return <main className="login-screen"><form className="login-card" onSubmit={confirmReset}><img src="/brand/arcat.png" alt="ARCAT · Agencia de Recaudación Catamarca"/><p>Elegí una nueva contraseña</p><label>Nueva contraseña<input autoFocus type="password" minLength={8} autoComplete="new-password" required value={password} onChange={(e)=>setPassword(e.target.value)}/></label><label>Repetir contraseña<input type="password" minLength={8} autoComplete="new-password" required value={passwordConfirmation} onChange={(e)=>setPasswordConfirmation(e.target.value)}/></label>{error&&<div className="notice notice--error">{error}</div>}<button className="primary" disabled={busy}>{busy?"Guardando…":"Cambiar contraseña"}</button><button type="button" className="login-public" onClick={()=>{history.replaceState(null,"",`${location.pathname}${location.search}`);setMode("login");}}>Volver al ingreso</button></form></main>;
  return <main className="login-screen"><form className="login-card" onSubmit={submit}><img src="/brand/arcat.png" alt="ARCAT · Agencia de Recaudación Catamarca"/><p>{initial?"Creá el Administrador inicial":"Panel interno de recaudación"}</p>{bootstrap?.required&&!bootstrap.available&&<div className="notice notice--error">El Administrador inicial debe crearse desde el servidor.</div>}{message&&<div className="notice notice--ok">{message}</div>}<label>Usuario<input autoFocus autoComplete="username" required value={username} onChange={(e)=>setUsername(e.target.value)}/></label>{initial&&<><label>Nombre<input required value={firstName} onChange={(e)=>setFirstName(e.target.value)}/></label><label>Apellido<input required value={lastName} onChange={(e)=>setLastName(e.target.value)}/></label><label>Correo<input type="email" autoComplete="email" required value={email} onChange={(e)=>setEmail(e.target.value)}/></label></>}<label>Contraseña<input type="password" minLength={8} autoComplete={initial?"new-password":"current-password"} required value={password} onChange={(e)=>setPassword(e.target.value)}/></label>{error&&<div className="notice notice--error">{error}</div>}<button className="primary" disabled={busy||bootstrap===null||(Boolean(bootstrap?.required)&&!bootstrap.available)}>{busy?(initial?"Creando…":"Ingresando…"):(initial?"Crear Administrador":"Ingresar")}</button>{!initial&&<button type="button" className="login-public" onClick={()=>{setMode("request");setError("");setMessage("");}}>¿Olvidaste tu contraseña?</button>}<button type="button" className="login-public" onClick={onPublic}>Ver pantalla pública</button></form></main>;
}

function odometerCadence(intervalSeconds:number){return Math.min(320,Math.max(44,40+intervalSeconds*4));}

function AnimatedMoney({value,style,intervalSeconds=1}:{value:number;style:string;intervalSeconds?:number}){
  let formatted=money.format(value);
  if(style==="ODOMETER"||style==="ROLLING"){
    const cents=Math.max(0,Math.round(value*100));
    formatted=money.format(cents/100);
    const characters=[...formatted];let place=0;
    const decimalIndex=formatted.lastIndexOf(",");
    const wheels=new Map<number,number>();
    for(let index=characters.length-1;index>=0;index-=1){
      if(/\d/.test(characters[index])){
        wheels.set(index,Math.floor(cents/Math.pow(10,place))%10);
        place+=1;
      }
    }
    return <strong className={`animated-amount animation-${style.toLowerCase()}`}>{characters.map((character,index)=>{
      const wheel=wheels.get(index);
      return wheel!==undefined?<span className={`odometer-slot ${index>decimalIndex&&decimalIndex>=0?"odometer-cent":""}`} key={index}><span className="odometer-digit" style={{animationDuration:`${Math.max(40,odometerCadence(intervalSeconds)-10)}ms`}} key={`${index}-${wheel}`}>{wheel}</span></span>:<span className={`amount-symbol ${index===decimalIndex?"decimal-separator":""}`} key={index}>{character}</span>;
    })}</strong>;
  }
  return <strong className={`animated-amount animation-${style.toLowerCase()}`}>{[...formatted].map((character,index)=><span key={`${index}-${character}-${value.toFixed(2)}`} className={/\d/.test(character)?"amount-digit":"amount-symbol"}>{character}</span>)}</strong>;
}

function AnimationPreview({config}:{config:ConfigForm}){
  const start=1234567.82;const target=1289076.47;const [value,setValue]=useState(start);
  const intervalSeconds=Math.max(1,Number(config.interval_value)||1)*({SECONDS:1,MINUTES:60,HOURS:3600}[config.interval_unit]||1);
  useEffect(()=>{
    let cancelled=false;let frame=0;const timers:number[]=[];
    const later=(callback:()=>void,delay:number)=>{const timer=window.setTimeout(()=>{if(!cancelled)callback();},delay);timers.push(timer);};
    const cycle=()=>{
      setValue(start);
      later(()=>{
        if(config.animation_style==="ODOMETER"&&config.adaptive_animation){
          const startCents=Math.round(start*100);const targetCents=Math.round(target*100);const width=Math.max(String(startCents).length,String(targetCents).length);
          const startDigits=String(startCents).padStart(width,"0").split("").map(Number);const targetDigits=String(targetCents).padStart(width,"0").split("").map(Number);
          const wheels=Array.from({length:width},(_,offset)=>width-1-offset).filter((index)=>startDigits[index]!==targetDigits[index]);
          const duration=Math.min(6500,Math.max(2400,1800+Math.log10(intervalSeconds+1)*900));const wheelDuration=duration/Math.max(1,wheels.length);const started=performance.now();let lastCents=startCents;
          const animate=(now:number)=>{if(cancelled)return;const elapsed=Math.min(duration,now-started);if(elapsed>=duration){setValue(target);later(cycle,1000);return;}const stage=Math.min(wheels.length-1,Math.floor(elapsed/wheelDuration));const activeIndex=wheels[stage];const stageProgress=(elapsed-stage*wheelDuration)/wheelDuration;const digits=[...startDigits];for(let index=0;index<stage;index+=1)digits[wheels[index]]=targetDigits[wheels[index]];const distance=(targetDigits[activeIndex]-startDigits[activeIndex]+10)%10;const visualSteps=10+distance;digits[activeIndex]=(startDigits[activeIndex]+Math.min(visualSteps,Math.floor(stageProgress*(visualSteps+1))))%10;const nextCents=Number(digits.join(""));if(nextCents!==lastCents){lastCents=nextCents;setValue(nextCents/100);}frame=requestAnimationFrame(animate);};
          frame=requestAnimationFrame(animate);return;
        }
        if(["FLIP","SLIDE","PULSE"].includes(config.animation_style)){setValue(target);later(cycle,1800);return;}
        const smooth=["ROLLING","FLUID"].includes(config.animation_style);const duration=config.animation_style==="INCREMENTAL"?1600:2200;const steps=smooth?36:(config.animation_style==="INCREMENTAL"?5:12);let step=0;
        const timer=window.setInterval(()=>{if(cancelled){window.clearInterval(timer);return;}step+=1;setValue(step>=steps?target:start+(target-start)*(step/steps));if(step>=steps){window.clearInterval(timer);later(cycle,1000);}},duration/steps);timers.push(timer);
      },500);
    };
    cycle();return()=>{cancelled=true;cancelAnimationFrame(frame);timers.forEach((timer)=>window.clearTimeout(timer));};
  },[config.animation_style,config.adaptive_animation,intervalSeconds]);
  const unitLabel=config.interval_unit==="SECONDS"?"segundos":config.interval_unit==="MINUTES"?"minutos":"horas";
  const previewName=config.animation_style==="ODOMETER"&&config.adaptive_animation?"Odómetro ajustado":animationNames[config.animation_style]||config.animation_style;
  return <section className="animation-preview"><div className="preview-copy"><span>Vista previa</span><b>{previewName}</b><small>Demostración acelerada · intervalo real: {config.interval_value} {unitLabel}</small></div><div className="preview-display"><p>Recaudación bruta</p><AnimatedMoney value={value} style={config.animation_style} intervalSeconds={intervalSeconds}/></div></section>;
}

function parsePasted(text:string, concepts:Concept[]) {
  const known = new Set(concepts.map((item) => item.code));
  const rows = [];
  const decimal = (value:string|undefined) => {
    let normalized=(value||"0").trim().replace(/\s/g,"").replace(/[^\d,.-]/g,"");
    if(normalized.includes(",")&&normalized.includes(".")){
      normalized=normalized.lastIndexOf(",")>normalized.lastIndexOf(".")?normalized.replace(/\./g,"").replace(",","."):normalized.replace(/,/g,"");
    }else if(normalized.includes(",")){normalized=normalized.replace(/\./g,"").replace(",", ".");}
    return normalized||"0";
  };
  for (const line of text.trim().split(/\r?\n/).filter(Boolean)) {
    const cells = line.split("\t");
    const code = (cells[0] || "").trim().toUpperCase();
    if (code === "CODIGO_CONCEPTO" || code === "TOTALES") continue;
    if (!known.has(code)) throw new Error(`Código no reconocido: ${code || "(vacío)"}`);
    rows.push({ code, receipt_count:cells[2] || 0, gross:decimal(cells[3]), commission:decimal(cells[4]), vat:decimal(cells[5]), other_expenses:decimal(cells[6]), observations:cells[7] || "" });
  }
  if (!rows.length) throw new Error("No se detectaron filas para cargar.");
  return rows;
}

function PublicScreen({ onExit }:{ onExit:()=>void }) {
  const [counter,setCounter] = useState<Counter|null>(null);
  const [online,setOnline] = useState(true);
  const [clock,setClock] = useState(() => new Date());
  const [displayAmount,setDisplayAmount] = useState(0);
  const [correction,setCorrection] = useState(false);
  const amountRef=useRef(0); const initializedRef=useRef(false);
  const refresh = useCallback(() => {
    fetch("/api/public/counter/").then((r) => { if (!r.ok) throw new Error(); return r.json(); })
      .then((value) => { setCounter(value); setOnline(true); }).catch(() => setOnline(false));
  }, []);
  useEffect(() => { refresh(); const timer=window.setInterval(refresh,Math.max(1000,(counter?.refresh_seconds||1)*1000)); return()=>window.clearInterval(timer); }, [refresh,counter?.refresh_seconds]);
  useEffect(() => { const timer=window.setInterval(()=>setClock(new Date()),1000); return()=>window.clearInterval(timer); }, []);
  useEffect(() => {
    if(!counter)return;
    const target=Number(counter.gross_visible||0);
    if(!initializedRef.current){initializedRef.current=true;amountRef.current=target;setDisplayAmount(target);return;}
    if(target===amountRef.current)return;
    if(target<amountRef.current){amountRef.current=target;setDisplayAmount(target);setCorrection(true);const warning=window.setTimeout(()=>setCorrection(false),8000);return()=>window.clearTimeout(warning);}
    const start=amountRef.current;
    if(["FLIP","SLIDE","PULSE"].includes(counter.animation_style||"")){amountRef.current=target;setDisplayAmount(target);return;}
    if(counter.animation_style==="FLUID"){
      const duration=Math.max(1000,(counter.refresh_seconds||1)*1000);const started=performance.now();let frame=0;let lastPaint=started-50;
      const animate=(now:number)=>{const progress=Math.min(1,(now-started)/duration);if(now-lastPaint>=50||progress===1){const next=start+(target-start)*progress;amountRef.current=next;setDisplayAmount(next);lastPaint=now;}if(progress<1)frame=requestAnimationFrame(animate);};
      frame=requestAnimationFrame(animate);return()=>cancelAnimationFrame(frame);
    }
    if(counter.animation_style==="ODOMETER"||counter.animation_style==="ROLLING"){
      const refreshMs=Math.max(1000,(counter.refresh_seconds||1)*1000);
      const configuredMs=Math.max(1000,(counter.animation_seconds||1)*1000);
      if(counter.animation_style==="ODOMETER"&&counter.adaptive_animation){
        const startCents=Math.round(start*100);
        const targetCents=Math.round(target*100);
        const width=Math.max(String(startCents).length,String(targetCents).length);
        const startDigits=String(startCents).padStart(width,"0").split("").map(Number);
        const targetDigits=String(targetCents).padStart(width,"0").split("").map(Number);
        const wheels=Array.from({length:width},(_,offset)=>width-1-offset).filter((index)=>startDigits[index]!==targetDigits[index]);
        if(!wheels.length){amountRef.current=target;setDisplayAmount(target);return;}
        const duration=refreshMs;
        const wheelDuration=duration/wheels.length;
        const started=performance.now();let frame=0;let lastCents=startCents;
        const animate=(now:number)=>{
          const elapsed=Math.min(duration,now-started);
          if(elapsed>=duration){amountRef.current=target;setDisplayAmount(target);return;}
          const stage=Math.min(wheels.length-1,Math.floor(elapsed/wheelDuration));
          const activeIndex=wheels[stage];
          const stageProgress=(elapsed-stage*wheelDuration)/wheelDuration;
          const digits=[...startDigits];
          for(let index=0;index<stage;index+=1)digits[wheels[index]]=targetDigits[wheels[index]];
          const distance=(targetDigits[activeIndex]-startDigits[activeIndex]+10)%10;
          const visualSteps=10+distance;
          digits[activeIndex]=(startDigits[activeIndex]+Math.min(visualSteps,Math.floor(stageProgress*(visualSteps+1))))%10;
          const nextCents=Number(digits.join(""));
          if(nextCents!==lastCents){lastCents=nextCents;const next=nextCents/100;amountRef.current=next;setDisplayAmount(next);}
          frame=requestAnimationFrame(animate);
        };
        frame=requestAnimationFrame(animate);
        return()=>cancelAnimationFrame(frame);
      }
      const duration=Math.min(configuredMs,refreshMs);
      const paintEvery=counter.animation_style==="ROLLING"?60:250;
      const started=performance.now();let frame=0;let lastPaint=started-paintEvery;
      const animate=(now:number)=>{const progress=Math.min(1,(now-started)/duration);if(now-lastPaint>=paintEvery||progress===1){const next=start+(target-start)*progress;amountRef.current=next;setDisplayAmount(next);lastPaint=now;}if(progress<1)frame=requestAnimationFrame(animate);};
      frame=requestAnimationFrame(animate);
      return()=>cancelAnimationFrame(frame);
    }
    const steps=Math.max(1,Math.ceil(Math.min(counter.animation_seconds||5,counter.refresh_seconds||1)));
    let step=0;
    const timer=window.setInterval(()=>{step+=1;const next=step>=steps?target:start+(target-start)*(step/steps);amountRef.current=next;setDisplayAmount(next);if(step>=steps)window.clearInterval(timer);},1000);
    return()=>window.clearInterval(timer);
  },[counter?.gross_visible,counter?.animation_seconds,counter?.refresh_seconds,counter?.animation_style,counter?.adaptive_animation]);
  const referenceDate=counter?.reference_date?new Date(`${counter.reference_date}T12:00:00`):null;
  const periodText=!referenceDate?"Sin período":counter?.display_period==="MONTHLY"?referenceDate.toLocaleDateString("es-AR",{month:"long",year:"numeric"}):counter?.display_period==="ANNUAL"?String(referenceDate.getFullYear()):referenceDate.toLocaleDateString("es-AR");
  return <main className="public-screen">
    <button className="public-exit" onClick={onExit}>Panel interno</button>
    <div className="public-mark"><img className="public-logo-img" src="/brand/arcat.png" alt="ARCAT · Agencia de Recaudación Catamarca"/></div>
    <time className="live-clock" dateTime={clock.toISOString()}><b>{clock.toLocaleTimeString("es-AR",{hour:"2-digit",minute:"2-digit",second:"2-digit"})}</b><span>{clock.toLocaleDateString("es-AR",{weekday:"long",day:"2-digit",month:"long",year:"numeric"})}</span></time>
    <section className="counter" aria-live="polite">
      <p>Recaudación bruta</p><AnimatedMoney value={displayAmount} style={counter?.animation_style||"COMBINED"} intervalSeconds={counter?.refresh_seconds||1}/>
      {correction&&<div className="correction-banner">Monto actualizado por corrección</div>}
      <div className="counter-meta">
        <span>{counter?.period_label||"Fecha de recaudación"}<br/><b className="period-value">{periodText}</b></span>
        <span>Última actualización<br/><b>{counter ? new Date(counter.updated_at).toLocaleTimeString("es-AR",{hour:"2-digit",minute:"2-digit"}) : "—"}</b></span>
      </div>
      {counter?.groups&&<div className="public-groups">{Object.entries(counter.groups).map(([group,value])=><div key={group}><span>{group.replaceAll("_"," ")}</span><b>{money.format(Number(value))}</b></div>)}</div>}
    </section>
    <div className={`connection ${online ? "" : "connection--offline"}`}>{online ? (counter?.is_progressing ? "Actualizando" : "Actualizado") : "Sin conexión · mostrando último valor"}</div>
  </main>;
}

export default function App() {
  const [view,setView] = useState<View>(() => location.hash === "#publica" ? "public" : "internal");
  const [authUser,setAuthUser]=useState<AuthUser|null>(null);const [authReady,setAuthReady]=useState(false);
  const [concepts,setConcepts] = useState<Concept[]>([]); const [channels,setChannels] = useState<Channel[]>([]); const [loads,setLoads] = useState<Load[]>([]);
  const [paste,setPaste] = useState(""); const [file,setFile] = useState<File|null>(null); const [busy,setBusy] = useState(false);
  const [notice,setNotice] = useState<{type:"ok"|"error";text:string}|null>(null);
  const [showConfig,setShowConfig] = useState(false); const [savingConfig,setSavingConfig] = useState(false);
  const [showUsers,setShowUsers]=useState(false);const [managedUsers,setManagedUsers]=useState<ManagedUser[]>([]);const [roles,setRoles]=useState<string[]>([]);const [savingUser,setSavingUser]=useState(false);
  const [userForm,setUserForm]=useState({username:"",password:"",first_name:"",last_name:"",email:"",role:"OPERADOR"});
  const [config,setConfig] = useState<ConfigForm|null>(null);
  const [form,setForm] = useState({ revenue_date:today,tgp_entry_date:today,channel_id:"",cutoff_date:today,cutoff_time:"23:59",publication_delay_minutes:"30" });
  const loadData = useCallback(async() => {
    const [a,b,c]=await Promise.all([fetch("/api/catalogs/"),fetch("/api/loads/"),fetch("/api/settings/progression/")]); if(!a.ok||!b.ok||!c.ok) throw new Error("No fue posible consultar la API");
    const catalog=await a.json(); const current=await c.json(); setConcepts(catalog.concepts); setChannels(catalog.channels); setLoads(await b.json());
    setConfig({ ...current, publication_delay_minutes:String(current.publication_delay_minutes),interval_value:String(current.interval_value),max_variation_percent:String(current.max_variation_percent),randomness_intensity_percent:String(current.randomness_intensity_percent),smoothing_intervals:String(current.smoothing_intervals),tv_animation_seconds:String(current.tv_animation_seconds),gamma:String(current.gamma) });
    setForm((old)=>({...old,channel_id:old.channel_id||String(catalog.channels[0]?.id||""),publication_delay_minutes:String(current.publication_delay_minutes)}));
  },[]);
  useEffect(()=>{fetch("/api/auth/csrf/").then(()=>fetch("/api/auth/me/")).then(async(response)=>{if(!response.ok)throw new Error();setAuthUser(await response.json());}).catch(()=>setAuthUser(null)).finally(()=>setAuthReady(true));},[]);
  useEffect(()=>{if(authUser)loadData().catch((e)=>setNotice({type:"error",text:e.message}));},[loadData,authUser]);
  const totals=useMemo(()=>loads.filter((x)=>x.status==="VALID").reduce((acc,item)=>({gross:acc.gross+Number(item.gross_total),net:acc.net+Number(item.net_total),receipts:acc.receipts+item.receipt_count}),{gross:0,net:0,receipts:0}),[loads]);

  async function submit(event:FormEvent) {
    event.preventDefault(); setBusy(true); setNotice(null);
    try {
      let body:BodyInit; const headers:HeadersInit={};
      if(file){const data=new FormData();Object.entries(form).forEach(([k,v])=>data.append(k,v));data.append("file",file);body=data;}
      else{headers["Content-Type"]="application/json";body=JSON.stringify({...form,rows:parsePasted(paste,concepts)});}
      headers["X-CSRFToken"]=decodeURIComponent(cookie("csrftoken"));
      const response=await fetch("/api/loads/",{method:"POST",headers,body});const result=await response.json();if(!response.ok)throw new Error(result.error||"No se pudo registrar la carga");
      setNotice({type:"ok",text:`Carga #${result.id} registrada. Bruto: ${money.format(Number(result.gross_total))}.`});setPaste("");setFile(null);await loadData();
    }catch(error){setNotice({type:"error",text:error instanceof Error?error.message:"Error inesperado"});}finally{setBusy(false);}
  }
  async function saveConfiguration(event:FormEvent) {
    event.preventDefault(); if(!config)return; setSavingConfig(true); setNotice(null);
    try{
      const response=await fetch("/api/settings/progression/",{method:"PATCH",headers:secureHeaders({"Content-Type":"application/json"}),body:JSON.stringify(config)});
      const result=await response.json();if(!response.ok)throw new Error(typeof result.error==="string"?result.error:JSON.stringify(result.error));
      setConfig({...config,...result,publication_delay_minutes:String(result.publication_delay_minutes),interval_value:String(result.interval_value),max_variation_percent:String(result.max_variation_percent),randomness_intensity_percent:String(result.randomness_intensity_percent),smoothing_intervals:String(result.smoothing_intervals),tv_animation_seconds:String(result.tv_animation_seconds),gamma:String(result.gamma)});
      setForm((old)=>({...old,publication_delay_minutes:String(result.publication_delay_minutes)}));
      setNotice({type:"ok",text:"Configuración guardada. Se aplicará a las nuevas cargas."});
    }catch(error){setNotice({type:"error",text:error instanceof Error?error.message:"No se pudo guardar"});}finally{setSavingConfig(false);}
  }
  const can=(permission:string)=>Boolean(authUser?.is_superuser||authUser?.permissions.includes(permission));
  const loadUsers=useCallback(async()=>{const response=await fetch("/api/users/");const result=await response.json();if(!response.ok)throw new Error(result.error||"No se pudieron consultar los usuarios");setManagedUsers(result.users);setRoles(result.roles);},[]);
  async function toggleUsers(){const next=!showUsers;setShowUsers(next);setShowConfig(false);if(next)try{await loadUsers();}catch(error){setNotice({type:"error",text:error instanceof Error?error.message:"No se pudieron consultar los usuarios"});}}
  async function createUser(event:FormEvent){event.preventDefault();setSavingUser(true);setNotice(null);try{const response=await fetch("/api/users/",{method:"POST",headers:secureHeaders({"Content-Type":"application/json"}),body:JSON.stringify(userForm)});const result=await response.json();if(!response.ok)throw new Error(result.error||"No se pudo crear el usuario");setUserForm({username:"",password:"",first_name:"",last_name:"",email:"",role:"OPERADOR"});setNotice({type:"ok",text:`Usuario ${result.username} creado correctamente.`});await loadUsers();}catch(error){setNotice({type:"error",text:error instanceof Error?error.message:"No se pudo crear el usuario"});}finally{setSavingUser(false);}}
  async function updateUser(user:ManagedUser,changes:Record<string,unknown>){setNotice(null);try{const response=await fetch(`/api/users/${user.id}/`,{method:"PATCH",headers:secureHeaders({"Content-Type":"application/json"}),body:JSON.stringify(changes)});const result=await response.json();if(!response.ok)throw new Error(result.error||"No se pudo actualizar el usuario");await loadUsers();}catch(error){setNotice({type:"error",text:error instanceof Error?error.message:"No se pudo actualizar el usuario"});}}
  async function logoutUser(){await fetch("/api/auth/logout/",{method:"POST",headers:secureHeaders()});setAuthUser(null);setConcepts([]);setChannels([]);setLoads([]);}
  if(location.hash.startsWith("#restablecer?"))return <LoginScreen onLogin={setAuthUser} onPublic={()=>{location.hash="publica";setView("public");}}/>;
  if(view==="public")return <PublicScreen onExit={()=>{location.hash="";setView("internal");}}/>;
  if(!authReady)return <main className="login-screen"><div className="login-card">Verificando acceso…</div></main>;
  if(!authUser)return <LoginScreen onLogin={setAuthUser} onPublic={()=>{location.hash="publica";setView("public");}}/>;
  return <main className="app-shell">
    <header className="topbar"><div className="internal-brand"><img src="/brand/arcat.png" alt="ARCAT · Agencia de Recaudación Catamarca"/><small>{authUser.full_name} · {authUser.roles[0]||"Sin rol"}</small></div><div className="top-actions">{can("auth.view_user")&&<button className="secondary" onClick={toggleUsers}>{showUsers?"Cerrar usuarios":"Usuarios"}</button>}{can("progression.change_progressionsettings")&&<button className="secondary" onClick={()=>{setShowConfig(!showConfig);setShowUsers(false);}}>{showConfig?"Cerrar configuración":"Configuración"}</button>}<button className="secondary secondary--strong" onClick={()=>{location.hash="publica";setView("public");}}>Abrir pantalla pública</button><button className="secondary" onClick={logoutUser}>Salir</button></div></header>
    <section className="page-heading"><div><p className="eyebrow">Panel interno · entorno local</p><h1>Recaudación</h1><p>Importá el detalle diario y controlá los totales antes de su publicación progresiva.</p></div><div className="api-ok"><i/> Sistema disponible</div></section>
    {showUsers&&can("auth.view_user")&&<section className="panel users-panel"><div className="panel-title"><div><span className="step">USR</span><h2>Usuarios y roles</h2></div><span>{managedUsers.length} usuarios</span></div><form className="user-form" onSubmit={createUser}><label>Usuario<input required value={userForm.username} onChange={(e)=>setUserForm({...userForm,username:e.target.value})}/></label><label>Nombre<input value={userForm.first_name} onChange={(e)=>setUserForm({...userForm,first_name:e.target.value})}/></label><label>Apellido<input value={userForm.last_name} onChange={(e)=>setUserForm({...userForm,last_name:e.target.value})}/></label><label>Correo<input type="email" required value={userForm.email} onChange={(e)=>setUserForm({...userForm,email:e.target.value})}/></label><label>Rol<select value={userForm.role} onChange={(e)=>setUserForm({...userForm,role:e.target.value})}>{(roles.length?roles:["ADMINISTRADOR","SUPERVISOR","OPERADOR"]).map((role)=><option key={role}>{role}</option>)}</select></label><label>Contraseña<input type="password" required minLength={8} autoComplete="new-password" value={userForm.password} onChange={(e)=>setUserForm({...userForm,password:e.target.value})}/></label><button className="primary" disabled={savingUser}>{savingUser?"Creando…":"Crear usuario"}</button></form>{notice&&<div className={`notice notice--${notice.type}`}>{notice.text}</div>}<div className="table-wrap users-table"><table><thead><tr><th>Usuario</th><th>Nombre</th><th>Correo</th><th>Rol</th><th>Estado</th><th>Acción</th></tr></thead><tbody>{managedUsers.map((user)=><tr key={user.id}><td><b>{user.username}</b>{user.is_superuser&&<small> Superusuario</small>}</td><td>{user.full_name}</td><td>{user.email||"—"}</td><td><select disabled={user.is_superuser} value={user.roles[0]||"OPERADOR"} onChange={(e)=>updateUser(user,{role:e.target.value})}>{(roles.length?roles:["ADMINISTRADOR","SUPERVISOR","OPERADOR"]).map((role)=><option key={role}>{role}</option>)}</select></td><td><span className={`badge ${user.is_active?"badge--valid":"badge--replaced"}`}>{user.is_active?"Activo":"Inactivo"}</span></td><td><button className="secondary compact" disabled={user.id===authUser.id||user.is_superuser} onClick={()=>updateUser(user,{is_active:!user.is_active})}>{user.is_active?"Desactivar":"Activar"}</button></td></tr>)}</tbody></table></div></section>}
    {showConfig&&config&&<form className="panel config-panel" onSubmit={saveConfiguration}>
      <div className="panel-title"><div><span className="step">CFG</span><h2>Configuración de la progresión</h2></div><span>Estos valores se copian en cada carga nueva</span></div>
      <div className="config-grid">
        <label className="wide">Algoritmo<select value={config.algorithm} onChange={(e)=>setConfig({...config,algorithm:e.target.value})}><option value="LINEAL_ALEATORIO_CONTROLADO">Lineal aleatorio controlado</option><option value="LINEAL">Lineal</option><option value="ACELERADO_AL_FINAL">Acelerado al final</option><option value="INMEDIATO">Inmediato</option></select></label>
        <label>Período a mostrar<select value={config.display_period} onChange={(e)=>setConfig({...config,display_period:e.target.value})}><option value="DAILY">Día determinado</option><option value="MONTHLY">Acumulado mensual</option><option value="ANNUAL">Acumulado anual</option></select></label>
        <label>Fecha de referencia<input type="date" value={config.reference_date} onChange={(e)=>setConfig({...config,reference_date:e.target.value})}/></label>
        <label>Demora inicial (min)<input type="number" min="0" max="1440" value={config.publication_delay_minutes} onChange={(e)=>setConfig({...config,publication_delay_minutes:e.target.value})}/></label>
        <label>Frecuencia de actualización<div className="unit-input"><input type="number" min="1" max="86400" value={config.interval_value} onChange={(e)=>setConfig({...config,interval_value:e.target.value})}/><select value={config.interval_unit} onChange={(e)=>setConfig({...config,interval_unit:e.target.value})}><option value="SECONDS">segundos</option><option value="MINUTES">minutos</option><option value="HOURS">horas</option></select></div></label>
        <label>Variación máxima (%)<input type="number" min="0" max="100" step="0.01" value={config.max_variation_percent} onChange={(e)=>setConfig({...config,max_variation_percent:e.target.value})}/></label>
        <label>Intensidad aleatoria (%)<input type="number" min="0" max="100" step="0.01" value={config.randomness_intensity_percent} onChange={(e)=>setConfig({...config,randomness_intensity_percent:e.target.value})}/></label>
        <label>Suavizado (intervalos)<input type="number" min="1" max="100" value={config.smoothing_intervals} onChange={(e)=>setConfig({...config,smoothing_intervals:e.target.value})}/></label>
        <label>Duración manual de animación (seg)<input type="number" min="0" max="86400" disabled={config.animation_style==="ODOMETER"&&config.adaptive_animation} value={config.tv_animation_seconds} onChange={(e)=>setConfig({...config,tv_animation_seconds:e.target.value})}/><small>{config.animation_style==="ODOMETER"&&config.adaptive_animation?"Automática: usa la frecuencia de actualización.":"Máximo: 24 horas."}</small></label>
        <label>Estilo de animación<select value={config.animation_style} onChange={(e)=>setConfig({...config,animation_style:e.target.value})}><option value="INCREMENTAL">Contador incremental</option><option value="ODOMETER">Odómetro</option><option value="COMBINED">Combinado</option><option value="FLIP">Flip institucional (recomendado)</option><option value="SLIDE">Deslizamiento suave</option><option value="PULSE">Pulso luminoso</option><option value="ROLLING">Rodillo simultáneo</option><option value="FLUID">Conteo fluido</option></select></label>
        <label>Gamma aceleración<input type="number" min="0.1" max="10" step="0.1" value={config.gamma} onChange={(e)=>setConfig({...config,gamma:e.target.value})}/></label>
      </div>
      <AnimationPreview config={config}/>
      <div className="toggles"><label><input type="checkbox" checked={config.counter_gross_only} onChange={(e)=>setConfig({...config,counter_gross_only:e.target.checked,show_group_breakdown:e.target.checked?false:config.show_group_breakdown})}/><span><b>Contador solo de recaudación bruta</b><small>Oculta el desglose en el Smart TV.</small></span></label><label><input type="checkbox" disabled={config.counter_gross_only} checked={config.show_group_breakdown} onChange={(e)=>setConfig({...config,show_group_breakdown:e.target.checked})}/><span><b>Mostrar desglose por grupo</b><small>Disponible al desactivar el modo de contador único.</small></span></label><label className={config.animation_style!=="ODOMETER"?"toggle-disabled":""}><input type="checkbox" disabled={config.animation_style!=="ODOMETER"} checked={config.adaptive_animation} onChange={(e)=>setConfig({...config,adaptive_animation:e.target.checked})}/><span><b>Odómetro ajustado</b><small>Reparte la frecuencia de actualización entre las ruedas: un intervalo mayor produce giros más lentos y uno menor, más rápidos.</small></span></label></div>
      {notice&&<div className={`notice notice--${notice.type}`}>{notice.text}</div>}
      <button className="primary" disabled={savingConfig}>{savingConfig?"Guardando…":"Guardar configuración"}</button>
    </form>}
    <section className="metrics"><article><span>Recaudación bruta vigente</span><strong>{money.format(totals.gross)}</strong></article><article><span>Recaudación neta</span><strong>{money.format(totals.net)}</strong></article><article><span>Comprobantes</span><strong>{totals.receipts.toLocaleString("es-AR")}</strong></article></section>
    <div className={`workspace ${!can("loads.add_revenueload")?"workspace--single":""}`}>
      {can("loads.add_revenueload")&&<form className="panel upload-panel" onSubmit={submit}>
        <div className="panel-title"><div><span className="step">01</span><h2>Nueva carga</h2></div><a href="/api/template/" download>Descargar plantilla</a></div>
        <div className="form-grid">
          <label>Fecha de recaudación<input type="date" required value={form.revenue_date} onChange={(e)=>setForm({...form,revenue_date:e.target.value})}/></label>
          <label>Ingreso a TGP<input type="date" required value={form.tgp_entry_date} onChange={(e)=>setForm({...form,tgp_entry_date:e.target.value})}/></label>
          <label>Canal de cobro<select required value={form.channel_id} onChange={(e)=>setForm({...form,channel_id:e.target.value})}>{channels.map((x)=><option key={x.id} value={x.id}>{x.name}</option>)}</select></label>
          <label>Fecha de corte<input type="date" required value={form.cutoff_date} onChange={(e)=>setForm({...form,cutoff_date:e.target.value})}/></label>
          <label>Hora de corte<input type="time" required value={form.cutoff_time} onChange={(e)=>setForm({...form,cutoff_time:e.target.value})}/></label>
          <label>Demora para publicar<input type="number" min="0" max="1440" required value={form.publication_delay_minutes} onChange={(e)=>setForm({...form,publication_delay_minutes:e.target.value})}/></label>
        </div>
        <div className="source-tabs"><label className={file?"source active":"source"}><input type="file" accept=".xlsx" onChange={(e)=>setFile(e.target.files?.[0]||null)}/><b>Subir Excel</b><span>{file?file.name:"Elegí la plantilla completa"}</span></label><span className="or">o</span><div className={!file?"source active":"source"}><b>Pegar desde Excel</b><span>Copiá las 8 columnas, incluido el código</span></div></div>
        <textarea disabled={!!file} value={paste} onChange={(e)=>setPaste(e.target.value)} placeholder={"INM\tINMOBILIARIO\t120\t1500000,00\t..."}/>
        <p className="hint">Se aceptan los códigos definidos en el catálogo. Los importes se normalizan a dos decimales.</p>
        {notice&&<div className={`notice notice--${notice.type}`}>{notice.text}</div>}
        <button className="primary" disabled={busy||(!file&&!paste.trim())}>{busy?"Validando…":"Validar y registrar carga"}</button>
      </form>}
      <aside className="panel catalog"><div className="panel-title"><div><span className="step">02</span><h2>Catálogo activo</h2></div></div><div className="catalog-list">{concepts.map((item)=><div key={item.code}><code>{item.code}</code><span>{item.name}<small>{item.group.replace("_"," ")}</small></span></div>)}</div></aside>
    </div>
    <section className="panel history"><div className="panel-title"><div><span className="step">03</span><h2>Últimas cargas</h2></div><span>{loads.length} registros</span></div><div className="table-wrap"><table><thead><tr><th>ID</th><th>Recaudación</th><th>Canal</th><th>Origen</th><th>Bruta</th><th>Neta</th><th>Comprobantes</th><th>Estado</th></tr></thead><tbody>{loads.map((item)=><tr key={item.id}><td>#{item.id}</td><td>{new Date(`${item.revenue_date}T12:00`).toLocaleDateString("es-AR")}</td><td>{item.channel}</td><td>{item.source_name}</td><td>{money.format(Number(item.gross_total))}</td><td>{money.format(Number(item.net_total))}</td><td>{item.receipt_count}</td><td><span className={`badge badge--${item.status.toLowerCase()}`}>{item.status==="VALID"?"Vigente":item.status}</span></td></tr>)}</tbody></table>{!loads.length&&<div className="empty">Todavía no hay cargas registradas.</div>}</div></section>
  </main>;
}
