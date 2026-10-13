// 用真实浏览器的方式测：headless chrome 打不开就用 fetch 模拟
const http = require('http');
function get(path){
  return new Promise((res,rej)=>{
    const req = http.get({host:'127.0.0.1',port:8848,path,timeout:8000},r=>{
      let b=''; r.on('data',d=>b+=d); r.on('end',()=>res({code:r.statusCode,len:b.length}));
    });
    req.on('error',e=>rej(e)); req.on('timeout',()=>{req.destroy();rej(new Error('timeout'))});
  });
}
(async()=>{
  for (const p of ['/','/api/state','/api/prompt/1','/video/off_xs01_t01_00014-audio.mp4']){
    try{ const r = await get(p); console.log(p.padEnd(46), r.code, r.len+'B'); }
    catch(e){ console.log(p.padEnd(46),'❌',e.message); }
  }
})();
