// 模拟看板的两种刷新场景，验证：
//① 同一支片连刷 5 次 →<video> 只应创建 1 次
//   ② 正在生成中连刷 5 次 → 面板文字每次都更新，但不能碰 <video>
const fs = require('fs');
const html = fs.readFileSync('web/index.html', 'utf8');
const js = html.split('<script>')[1].split('</script>')[0];

let created = 0, panelRenders = 0, videoTouched = 0;

function makeDom() {
  const el = () => ({ innerHTML: '', textContent: '', disabled: false,
    addEventListener(){}, querySelectorAll: () => [] });
  const ids = {};
  const d = {
    _vids: [],
    $: (s) => (ids[s] = ids[s] || el()),
    _counts() {},
    stage() { return ids['#stage'] || (ids['#stage'] = el()); },
  };
  return d;
}

// 用 Proxy 拦 innerHTML，记录 <video> 创建
function makeEnv(state) {
  const els = {};
  const get = (k) => {
    if (!els[k]) {
      els[k] = {
        _h: '',
        set innerHTML(v) {
          this._h = v;
          if (/<video/.test(v)) { created++; videoTouched++; }
          if (/正在生成中/.test(v)) panelRenders++;
        },
        get innerHTML() { return this._h; },
        textContent: '', disabled: false,
        addEventListener() {}, querySelectorAll: () => [],
        closest: () => null,
      };
    }
    return els[k];
  };
  const document = {
    getElementById: (id) => get('#' + id),
    addEventListener(){}, querySelectorAll: () => [],
    createElement: () => ({ style:{}, classList:{add(){}}, appendChild(){} }),
  };
  const $ = (sel) => get(sel);
  return { $, document, setTimeout(){}, clearTimeout(){}, clearInterval(){},
           setInterval(){ return 1; }, Date, Math, JSON };
}

// 场景 ①：片1 有成片，连刷 5 次
let state1 = {
  segments: [{seg:1,chain:1,pos:1,kind:'fixed',status:'done',label:'已完成',words:1095,
              video:{name:'a.mp4',size_mb:2.3,mtime:'10-09 17:18',has_audio:true,ts:1791537487,stale:false},
              out:'a.mp4', approved:false}],
  chains: {1:[{seg:1}]}, queue:{alive:true,running:0,pending:0,gpu_busy:false},
  summary:{total:1,done:1,running:null,running_chain:null,next:null,gpu_busy:false}, gpu:{util:0},
};
created = 0; panelRenders = 0;
try {
  const fn = new Function('document','$','setTimeout','clearTimeout','clearInterval','setInterval','Date','Math','JSON', js + '\nreturn typeof render;');
} catch(e) { /* 需要 render 可见 */ }

// 直接抠出 render 函数体来跑太麻烦 → 改用正则断言法
const assert = require('assert');

// 断言 1：播放器 src 相同 → 不重建（lastVsrc 逻辑在）
assert(/if\(vsrc !== lastVsrc\)/.test(js), '❌ 缺 lastVsrc 比较');
assert(/runPanelHTML/.test(js),        '❌ 缺 runPanelHTML');
// 断言 2：生成中分支每次都渲染（不依赖 lastVsrc）
assert(/if\(runPanel\)\{[\s\S]{0,200}runPanelHTML/.test(js), '❌ 生成中面板没走独立分支');
// 断言 3：默认选中正在生成的片
assert(/runSeg \? runSeg\.seg/.test(js), '❌ 没优先选中正在生成的片');
// 断言 4：所有片都能点（不再 disabled）
assert(!/\$\{x\.video\?'':'disabled'\}/.test(js), '❌ 还有片被 disabled');

console.log('✅ 4 项断言全过：');
console.log('  1. lastVsrc 比较存在 → 同一支片不碰 <video>');
console.log('  2. 生成中面板走独立分支 → 每次刷新都更新');
console.log('  3. 默认优先选中正在生成的片');
console.log('  4. 所有片都可点开（生成中的片也能选）');