import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { Presentation, PresentationFile } from '@oai/artifact-tool';

const workspaceDir = '/Users/dhruv/Tredence_H4ck';
const buildDir = path.join(workspaceDir, '.codex-build/shelfsense-presentation');
const skillDir = '/Users/dhruv/.codex/plugins/cache/openai-primary-runtime/presentations/26.1020.11127/skills/presentations';
const runtimePython = '/Users/dhruv/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3';
const finalPath = path.join(workspaceDir, 'deliverables/ShelfSense_AI_Mentor_Ready_Project_Presentation_v2.pptx');
const candidatePath = path.join(buildDir, 'ShelfSense_AI_candidate.pptx');
const outDir = path.join(buildDir, 'renders');

const A = {
  ink: '#0d0f12', panel: '#171b22', slate: '#222835', white: '#f8fafc', muted: '#a8b1c1',
  line: '#3b4555', teal: '#2dd4bf', cyan: '#38bdf8', orange: '#f59e0b', rose: '#fb7185',
  green: '#6ee7b7', pale: '#e2e8f0', navy: '#111827', dim: '#708097'
};
const FONT = 'Aptos';
const assets = {
  shelf: path.join(workspaceDir, 'image-parsing/tests/fixtures/compliance/pipeline-verification/shelf_photo.png'),
  annotated: path.join(workspaceDir, 'backend/uploads/image_processing/outputs/7/3a6f2153432e4bc7986eab152f10d97c_annotated.jpg'),
  dashboard: '/Users/dhruv/.gemini/antigravity-ide/brain/a392ed68-b77d-43a0-9d68-3ae758d8881a/dashboard_desktop.png',
  designer: '/Users/dhruv/.gemini/antigravity-ide/brain/a392ed68-b77d-43a0-9d68-3ae758d8881a/designer_desktop.png',
  milk: path.join(workspaceDir, 'backend/uploads/image_processing/outputs/7/cutouts/products/crop_0051.jpg'),
  lays: path.join(workspaceDir, 'backend/uploads/image_processing/outputs/7/cutouts/products/crop_0021.jpg'),
  juice: path.join(workspaceDir, 'backend/uploads/image_processing/outputs/7/cutouts/products/crop_0037.jpg'),
  laundry: path.join(workspaceDir, 'backend/uploads/image_processing/outputs/7/cutouts/products/crop_0059.jpg'),
  juicePack: path.join(workspaceDir, 'sample_assets/images/orange_juice_carton.png'),
  laundryPack: path.join(workspaceDir, 'sample_assets/images/laundry_bottle.png'),
  chipsPack: path.join(workspaceDir, 'sample_assets/images/crispy_chips_bag.png')
};

async function writeBlob(file, blob) { await fs.writeFile(file, new Uint8Array(await blob.arrayBuffer())); }
const imageBytes = new Map();
async function preloadImages() {
  for (const source of Object.values(assets)) {
    imageBytes.set(source, await fs.readFile(source));
  }
}
function box(slide, x, y, w, h, fill, radius = 14, line = 'none') {
  return slide.shapes.add({ geometry: 'roundRect', position: { left:x, top:y, width:w, height:h }, fill,
    line: line === 'none' ? { style:'solid', fill:'none', width:0 } : { style:'solid', fill:line, width:1 }, borderRadius: radius });
}
function txt(slide, text, x, y, w, h, size=20, color=A.white, opts={}) {
  const s = slide.shapes.add({ geometry:'textbox', position:{ left:x, top:y, width:w, height:h }, fill:'none', line:{style:'solid',fill:'none',width:0}, name:opts.name });
  s.text = text; s.text.style = { fontFamily:FONT, fontSize:size, color, bold:opts.bold ?? false, italic:opts.italic ?? false, align:opts.align ?? 'left', verticalAlignment: opts.va ?? 'top' };
  s.text.insets = opts.insets ?? 0;
  return s;
}
function line(slide, x1, y1, x2, y2, color=A.line, width=2) { return slide.shapes.add({ geometry:'line', position:{left:x1,top:y1,width:x2-x1,height:y2-y1}, fill:'none', line:{style:'solid',fill:color,width} }); }
function img(slide, source, x, y, w, h, alt, fit='cover') {
  const contentType = source.toLowerCase().endsWith('.png') ? 'image/png' : 'image/jpeg';
  return slide.images.add({ blob:imageBytes.get(source), contentType, alt, fit, geometry:'roundRect', borderRadius:14, position:{left:x,top:y,width:w,height:h} });
}
function tag(slide, text, x, y, w, fill, color=A.ink) { const b=box(slide,x,y,w,25,fill,12); txt(slide,text,x+10,y+5,w-20,16,11,color,{bold:true}); return b; }
function title(slide, num, heading, sub='') { txt(slide, String(num).padStart(2,'0'), 58, 38, 44, 20, 12, A.teal, {bold:true}); txt(slide,heading,58,68,1080,46,31,A.white,{bold:true}); if(sub) txt(slide,sub,58,118,1080,26,15,A.muted); line(slide,58,154,1222,154,A.line,1); }
function footer(slide, num) { txt(slide,'ShelfSense AI  |  Mentor review',58,684,300,17,11,A.dim); txt(slide,`${String(num).padStart(2,'0')}  /  16`,1130,684,90,17,11,A.dim,{align:'right'}); }
function note(slide, sources) { slide.speakerNotes.text = `Evidence / sources:\n${sources.join('\n')}`; slide.speakerNotes.setVisible(true); }
function bullet(slide, text, x, y, w, color=A.pale, accent=A.teal, size=17) { box(slide,x,y+8,7,7,accent,4); txt(slide,text,x+17,y,w, size*1.45,size,color); }
function status(slide, label, x,y,w, fill,color) { tag(slide,label,x,y,w,fill,color); }

async function main() {
  await fs.mkdir(outDir,{recursive:true});
  await preloadImages();
  const p = Presentation.create({ slideSize:{width:1280,height:720} });

  // 1 cover
  { const s=p.slides.add(); s.background.fill=A.ink;
    img(s,assets.shelf,640,0,640,720,'Four-row shelf fixture used for pipeline verification');
    box(s,0,0,700,720,'#0d0f12');
    box(s,605,0,130,720,'#0d0f12');
    txt(s,'ShelfSense AI',72,84,520,42,22,A.teal,{bold:true});
    txt(s,'AI-Powered Supermarket Shelf &\nPlanogram Compliance',72,138,580,138,46,A.white,{bold:true});
    txt(s,'From physical planogram design to evidence-backed shelf-photo auditing',72,300,510,54,22,A.muted);
    line(s,72,398,392,398,A.orange,4);
    txt(s,'Prepared for mentor review\nDhruv  |  October 2026',72,430,360,56,16,A.pale);
    tag(s,'Working prototype + controlled fixture evidence',72,550,310,'#173a39',A.green);
    note(s,[
      'Repository fixture: image-parsing/tests/fixtures/compliance/pipeline-verification/shelf_photo.png',
      'Product and implementation evidence: docs/shared/ARCHITECTURE.md; docs/shared/COMPLIANCE_ROADMAP.md'
    ]);
  }

  // 2 executive summary
  { const s=p.slides.add(); s.background.fill=A.ink; title(s,2,'Executive summary','What has been built, and what the evidence supports');
    txt(s,'ShelfSense converts a planogram into a frozen audit reference, processes a shelf photograph, and produces an explainable compliance report.',58,190,710,76,25,A.white,{bold:true});
    bullet(s,'Planogram designer stores shelf geometry in centimetres and prevents overlap or out-of-bounds placement.',64,303,650);
    bullet(s,'Image pipeline detects shelf elements, extracts product crops, maps rows and positions, then matches only the shelf-scoped catalogue.',64,359,650);
    bullet(s,'Compliance report preserves evidence, locations, confidence gates, and operator dispositions.',64,415,650);
    box(s,825,198,350,315,A.panel,18,A.line);
    txt(s,'Verified fixture result',855,228,280,26,15,A.teal,{bold:true});
    txt(s,'54',855,270,90,60,52,A.white,{bold:true}); txt(s,'correct facings',952,292,150,24,16,A.muted);
    line(s,855,344,1140,344,A.line,1);
    txt(s,'1',855,366,52,46,36,A.orange,{bold:true}); txt(s,'misplaced Yellow Lays',916,375,200,25,15,A.pale);
    txt(s,'1',855,417,52,46,36,A.rose,{bold:true}); txt(s,'empty facing detected',916,426,200,25,15,A.pale);
    txt(s,'10 low-confidence boxes withheld from identity and quantity decisions',855,484,270,42,13,A.muted);
    tag(s,'Status: implemented, thresholds provisional',855,545,268,'#332b18',A.orange);
    footer(s,2); note(s,['backend/uploads/image_processing/outputs/7/analysis.json', 'backend/uploads/image_processing/outputs/7/compliance_audit.json', 'docs/shared/COMPLIANCE_ROADMAP.md']);
  }

  // 3 problem
  { const s=p.slides.add(); s.background.fill=A.ink; title(s,3,'Problem statement and motivation','A shelf photo contains visual evidence. A planogram contains physical expectations. Compliance requires a defensible comparison.');
    img(s,assets.shelf,58,192,350,418,'Original controlled shelf photo');
    txt(s,'Observed shelf',58,625,350,24,15,A.pale,{bold:true,align:'center'});
    box(s,474,211,2,366,A.line,0);
    txt(s,'Why this is difficult',525,194,500,30,23,A.white,{bold:true});
    bullet(s,'A detector can locate packaging without proving the exact catalogue identity.',525,247,610,A.pale,A.orange);
    bullet(s,'Rows and x-positions in pixels must align with an expected physical shelf layout.',525,315,610,A.pale,A.cyan);
    bullet(s,'Lookalike packaging, occlusion, perspective, and low-confidence detections must remain reviewable rather than turn into false alerts.',525,383,610,A.pale,A.rose);
    box(s,525,482,565,87,'#16222b',14,'#284253');
    txt(s,'Decision rule',548,501,120,18,13,A.teal,{bold:true});
    txt(s,'Claim “missing” or “misplaced” only when identity and calibrated position support it.',548,528,500,32,18,A.white,{bold:true});
    footer(s,3); note(s,['Fixture image: image-parsing/tests/fixtures/compliance/pipeline-verification/shelf_photo.png', 'Compliance decision behavior: backend/app/services/compliance_service.py']);
  }

  // 4 status inventory
  { const s=p.slides.add(); s.background.fill=A.ink; title(s,4,'Feature-status inventory','The presentation separates production code, controlled-fixture evidence, and open validation work');
    const rows=[
      ['Planogram designer and cm-based placement rules','Implemented','FastAPI, SQLite, Next.js'],
      ['YOLO product, empty-space and row parsing','Implemented','Weights and inference pipeline present'],
      ['Cutouts, shelf-scoped CLIP matching, cluster consensus','Implemented','Thresholds remain provisional'],
      ['Row/x-coordinate mapping and audit report','Implemented','Controlled fixture covered'],
      ['OCR price-label flow','Implemented adapter','Runtime smoke check, accuracy unevaluated'],
      ['YOLO product training / mAP evaluation','Not evidenced','No training result claimed'],
      ['Variant-level accuracy calibration','Open','Needs labelled crops and shelf fixtures']
    ];
    txt(s,'Capability',74,195,495,24,15,A.muted,{bold:true}); txt(s,'Status',640,195,180,24,15,A.muted,{bold:true}); txt(s,'Evidence / caveat',847,195,330,24,15,A.muted,{bold:true}); line(s,58,223,1218,223,A.line,1);
    rows.forEach((r,i)=>{const y=240+i*56; if(i%2===0) box(s,58,y-4,1160,48,'#12161d',8); txt(s,r[0],74,y+8,510,34,16,A.white,{bold:i<4}); const isOpen=r[1]==='Open'||r[1]==='Not evidenced'; const isPartial=r[1]==='Implemented adapter'; status(s,r[1],640,y+7, isPartial?156:130, isOpen?'#3a222b':isPartial?'#3a3019':'#163a34',isOpen?A.rose:isPartial?A.orange:A.green); txt(s,r[2],847,y+8,335,34,14,A.pale);});
    footer(s,4); note(s,['docs/shared/COMPLIANCE_ROADMAP.md', 'image-parsing/README.md', 'backend/PRICE_TAG_DETECTION_SETUP.md', 'image-parsing/MODEL_SETUP.md']);
  }

  // 5 workflow
  { const s=p.slides.add(); s.background.fill=A.ink; title(s,5,'End-to-end workflow','Actual source modules appear below each stage. Orange labels identify evidence gates or provisional thresholds.');
    const steps=[['Planogram\n+ shelf','Designer + snapshot','A.teal'],['Shelf photo','Input image job','A.cyan'],['YOLO parse','Rows, products, empty','A.teal'],['Cutouts + match','Color gate + CLIP','A.orange'],['Map to cm','Rows + x-span','A.cyan'],['Audit report','Findings + evidence','A.green']];
    const xs=[58,252,446,640,834,1028];
    steps.forEach((st,i)=>{box(s,xs[i],282,160,112,'#171d26',16,A.line); txt(s,st[0],xs[i]+14,300,132,42,18,A.white,{bold:true,align:'center'}); txt(s,st[1],xs[i]+12,354,136,23,12,A.muted,{align:'center'}); if(i<steps.length-1) {line(s,xs[i]+160,338,xs[i+1]-8,338,A.dim,2); txt(s,'›',xs[i]+169,318,22,30,26,A.teal,{bold:true});}});
    const files=['planogram_service.py','image_processing_service.py','pipeline.py','cutout_service.py','position_calibration.py','compliance_reporting_service.py'];
    files.forEach((f,i)=>txt(s,f,xs[i]-8,418,176,36,12,A.dim,{align:'center'}));
    box(s,122,510,1036,74,'#16222b',14,'#284253');
    txt(s,'Evidence gates',146,530,130,22,14,A.orange,{bold:true});
    txt(s,'Detection ≥ 0.60 for product crops. Catalogue decisions require shelf-scoped candidates. Missing-stock claims require calibrated positions.',300,526,820,35,16,A.pale);
    footer(s,5); note(s,['backend/app/services/image_processing_service.py', 'image-parsing/src/shelf_image_parsing/pipeline.py', 'backend/app/services/cutout_service.py', 'backend/app/services/position_calibration.py', 'backend/app/services/compliance_reporting_service.py']);
  }

  // 6 system architecture
  { const s=p.slides.add(); s.background.fill=A.ink; title(s,6,'System architecture','A modular monolith with local persistence and a separate image-parsing package');
    const frontend=box(s,58,216,300,256,'#14232c',16,'#245064'); const backend=box(s,487,216,300,256,'#181d28',16,'#394153'); const storage=box(s,916,216,300,256,'#162b29',16,'#2d5e56');
    txt(s,'Frontend',82,242,235,28,22,A.cyan,{bold:true}); txt(s,'Next.js + TypeScript\nDashboard, Planogram Designer\nAnalysis and compliance report',82,294,244,90,17,A.pale);
    txt(s,'Client API\napi.ts',82,409,220,26,14,A.muted);
    txt(s,'Backend',511,242,235,28,22,A.teal,{bold:true}); txt(s,'FastAPI + SQLAlchemy\nREST routes, audit snapshots\nCompliance and reporting services',511,294,244,90,17,A.pale);
    txt(s,'image-parsing package\nYOLO + OpenCV + CV utilities',511,409,250,36,14,A.muted);
    txt(s,'Persistence',940,242,235,28,22,A.green,{bold:true}); txt(s,'SQLite database\nLocal uploads and derived crops\nVersioned JSON / ZIP exports',940,294,244,90,17,A.pale);
    txt(s,'Packshots + embeddings\nAudit evidence',940,409,250,36,14,A.muted);
    line(s,358,344,487,344,A.cyan,3); txt(s,'REST / multipart',374,316,98,20,12,A.muted,{align:'center'}); line(s,787,344,916,344,A.green,3); txt(s,'paths + JSON',804,316,94,20,12,A.muted,{align:'center'});
    box(s,242,539,796,54,'#101820',14,'#284253'); txt(s,'Invariant: physical centimetres govern shelf layout. Frontend pixels only project that geometry for interaction and display.',270,555,740,24,16,A.white,{bold:true,align:'center'});
    footer(s,6); note(s,['docs/shared/ARCHITECTURE.md', 'backend/app/main.py', 'frontend/src/lib/api.ts', 'backend/app/db/models.py']);
  }

  // 7 inputs & snapshot
  { const s=p.slides.add(); s.background.fill=A.ink; title(s,7,'Inputs and frozen audit reference','Each processing job captures the planogram state and the relevant shelf catalogue before analysis begins');
    const blocks=[['Planogram','Shelf width, rows, product placements, facings','Expected physical arrangement'],['Shelf photograph','Original uploaded image','Observed visual evidence'],['Audit snapshot','Expected facing slots + shelf-specific catalogue','Immutable comparison frame'],['Packshots + metadata','Name, SKU, category, price, embeddings','Candidate identity evidence']];
    const y=[205,292,379,466];
    blocks.forEach((b,i)=>{box(s,72,y[i],484,64,'#151a23',12,A.line); txt(s,b[0],92,y[i]+13,140,20,16,[A.teal,A.cyan,A.orange,A.green][i],{bold:true}); txt(s,b[1],232,y[i]+12,300,21,14,A.white); txt(s,b[2],232,y[i]+34,300,18,12,A.muted);});
    box(s,636,207,528,320,'#121822',20,'#2c4051'); txt(s,'Why shelf-scoped candidates matter',672,237,420,28,23,A.white,{bold:true});
    bullet(s,'The matcher excludes unrelated catalogue products captured outside the selected shelf.',672,292,430,A.pale,A.teal,16);
    bullet(s,'It preserves the actual candidate set that existed when the audit started.',672,354,430,A.pale,A.orange,16);
    bullet(s,'It makes a weak visual match an explicit review state rather than a confident global-catalogue guess.',672,416,430,A.pale,A.rose,16);
    tag(s,'Snapshot-bound analysis cache',672,480,215,'#173a39',A.green);
    footer(s,7); note(s,['docs/shared/ARCHITECTURE.md', 'docs/shared/COMPLIANCE_ROADMAP.md', 'backend/app/services/image_processing_service.py', 'backend/app/services/cutout_service.py']);
  }

  // 8 YOLO and cutouts
  { const s=p.slides.add(); s.background.fill=A.ink; title(s,8,'Shelf parsing, row understanding, and cutout extraction','YOLO weights detect product / empty-space and shelf-row evidence. Product detection and exact identity remain separate tasks.');
    img(s,assets.annotated,58,188,420,440,'YOLO annotated Output 7 shelf photo');
    txt(s,'Stored annotated output',58,642,420,22,14,A.pale,{align:'center',bold:true});
    box(s,535,198,630,110,'#171d26',16,A.line); txt(s,'Current parsing behavior',562,221,220,25,18,A.teal,{bold:true}); txt(s,'Segments shelf rows, detects product and empty-space proposals, filters product crops below 0.60 confidence, and retains excluded boxes as uncertainty geometry.',562,254,565,38,15,A.pale);
    txt(s,'Detection  →  Crop  →  Identity evidence',535,342,590,26,20,A.white,{bold:true});
    const cropPaths=[assets.milk,assets.lays,assets.juice,assets.laundry];
    cropPaths.forEach((p,i)=>{img(s,p,545+i*145,392,117,130,`Extracted product crop ${i+1}`);});
    const labels=['example crop','example crop','example crop','example crop']; labels.forEach((l,i)=>txt(s,l,545+i*145,535,117,18,11,A.muted,{align:'center'}));
    box(s,535,582,630,55,'#2e2328',12,'#613945'); txt(s,'Important boundary: a bounding box proves location, not the exact SKU or variant.',558,599,570,24,17,A.rose,{bold:true});
    footer(s,8); note(s,['Annotated output: backend/uploads/image_processing/outputs/7/3a6f2153432e4bc7986eab152f10d97c_annotated.jpg', 'image-parsing/src/shelf_image_parsing/detector.py', 'image-parsing/src/shelf_image_parsing/row_segmenter.py', 'backend/app/services/cutout_service.py']);
  }

  // 9 matching
  { const s=p.slides.add(); s.background.fill=A.ink; title(s,9,'Catalogue matching and variant identification','Exact catalogue matching uses crop-level evidence. Cluster consensus helps repeated shelf items but does not replace per-crop identity.');
    const x=[70,330,590,850]; const head=['1. Candidate gate','2. Visual ranking','3. Decision state','4. Cluster consensus']; const body=['Use the frozen shelf catalogue only.\nColor compatibility filters candidates first.','Compare crop embedding with packshot embeddings using CLIP cosine similarity.','Accept only when score and margin clear provisional thresholds. Otherwise keep reviewable.','Consolidate only a clear same-row catalogue majority. Preserve individual matches.'];
    x.forEach((xx,i)=>{box(s,xx,236,205,260,'#161c25',16,A.line); txt(s,head[i],xx+18,261,170,48,19,[A.teal,A.cyan,A.orange,A.green][i],{bold:true}); txt(s,body[i],xx+18,330,168,112,15,A.pale); if(i<3) {txt(s,'›',xx+215,338,32,34,28,A.dim,{bold:true,align:'center'});}});
    box(s,70,546,1045,63,'#111b22',14,'#2b5360'); txt(s,'Current state',93,566,106,20,14,A.cyan,{bold:true}); txt(s,'CLIP score 0.90 and ambiguity margin 0.03 are present in code but require controlled crop-level calibration. No trained YOLO SKU-classifier or variant accuracy metric is claimed.',220,561,860,34,16,A.white);
    footer(s,9); note(s,['backend/app/services/cutout_service.py', 'backend/app/services/product_matching/candidate_filtering.py', 'backend/app/services/product_matching/cluster_consensus.py', 'docs/shared/COMPLIANCE_ROADMAP.md']);
  }

  // 10 coordinates and audit
  { const s=p.slides.add(); s.background.fill=A.ink; title(s,10,'Planogram coordinate mapping and compliance decisions','The audit compares expected facing slots with observed, calibrated crop positions in the same row coordinate system');
    box(s,70,205,530,314,'#151b23',16,A.line); txt(s,'Expected planogram',98,231,220,26,19,A.teal,{bold:true});
    for(let r=0;r<4;r++){txt(s,`Row ${r+1}`,99,280+r*53,62,18,13,A.muted); box(s,177,271+r*53,380,29,['#4d3218','#4d4618','#18424b','#223e36'][r],7); for(let k=0;k<15;k++) line(s,177+(k+1)*25.3,271+r*53,177+(k+1)*25.3,300+r*53,'#ffffff33',1);}
    txt(s,'15 expected facings per row  |  width 120 cm  |  top-to-bottom row index',98,480,430,20,13,A.pale);
    box(s,674,205,530,314,'#151b23',16,A.line); txt(s,'Observed shelf',702,231,220,26,19,A.cyan,{bold:true});
    for(let r=0;r<4;r++){txt(s,`Row ${r+1}`,703,280+r*53,62,18,13,A.muted); box(s,781,271+r*53,380,29,['#4d3218','#4d4618','#18424b','#223e36'][r],7); for(let k=0;k<15;k++) line(s,781+(k+1)*25.3,271+r*53,781+(k+1)*25.3,300+r*53,'#ffffff33',1);}
    box(s,781+10*25.3,271,25.3,29,A.rose,3); box(s,781+13*25.3,324,25.3,29,'#0d0f12',3,'#f59e0b');
    txt(s,'red = misplaced Lays',702,480,150,18,13,A.rose); txt(s,'orange outline = empty facing',882,480,245,18,13,A.orange);
    box(s,132,566,1016,48,'#2e2328',12,'#613945'); txt(s,'Conservative rule: when calibration is unavailable, the audit reports “needs review” instead of inferring a definitive missing-stock result.',156,580,965,22,15,A.white,{bold:true,align:'center'});
    footer(s,10); note(s,['image-parsing/tests/fixtures/compliance/pipeline-verification/manifest.json', 'backend/app/services/position_calibration.py', 'backend/app/services/compliance_service.py']);
  }

  // 11 product UI
  { const s=p.slides.add(); s.background.fill=A.ink; title(s,11,'Working product interface','The frontend persists planograms and image-processing outputs through the FastAPI backend');
    img(s,assets.dashboard,58,188,552,388,'Actual ShelfSense dashboard screenshot'); img(s,assets.designer,670,188,552,388,'Actual Planogram Designer screenshot');
    txt(s,'Dashboard',58,596,552,24,16,A.cyan,{bold:true,align:'center'}); txt(s,'Planogram Designer',670,596,552,24,16,A.teal,{bold:true,align:'center'});
    txt(s,'The designer uses a dark SaaS shell, hierarchy outliner, physical shelf canvas, and direct API synchronization. The analysis flow renders cutout and compliance evidence in the same application.',90,640,1090,32,15,A.pale,{align:'center'});
    footer(s,11); note(s,['UI screenshots: /Users/dhruv/.gemini/antigravity-ide/brain/a392ed68-b77d-43a0-9d68-3ae758d8881a/dashboard_desktop.png and designer_desktop.png', 'frontend/src/app/page.tsx', 'frontend/src/app/designer/page.tsx', 'frontend/src/app/analysis/page.tsx']);
  }

  // 12 scenario evidence
  { const s=p.slides.add(); s.background.fill=A.ink; title(s,12,'Controlled four-row fixture evidence','The fixture provides scenario-level acceptance rules. It does not establish detector precision, recall, or calibrated measurement accuracy.');
    img(s,assets.shelf,58,188,320,420,'Original controlled verification shelf');
    txt(s,'Fixture planogram',425,191,250,25,20,A.white,{bold:true});
    const data=[['Row 1','Amul Milk Chocolate','15 expected','1 Yellow Lays interleaved'],['Row 2','Yellow Lays','15 expected','14 reported, one empty facing'],['Row 3','Orange Juice','15 expected','Full, ±2 facings tolerated'],['Row 4','Fresh Laundry Liquid','15 expected','Full and correctly arranged']];
    data.forEach((d,i)=>{const y=234+i*78; box(s,425,y,735,63,i===0?'#21191b':'#151a23',12,A.line); txt(s,d[0],443,y+12,60,18,14,A.muted,{bold:true}); txt(s,d[1],518,y+10,230,20,16,A.white,{bold:true}); txt(s,d[2],518,y+34,170,16,12,A.muted); txt(s,d[3],760,y+17,365,28,14,i<2?[A.rose,A.orange][i]:A.pale,{bold:i<2});});
    box(s,425,570,735,57,'#173a39',12,'#2c655a'); txt(s,'Regression target: report one misplaced Lays on Row 1 and one empty Lays facing on Row 2 without false low-stock alerts.',449,586,680,25,15,A.green,{bold:true,align:'center'});
    footer(s,12); note(s,['image-parsing/tests/fixtures/compliance/pipeline-verification/manifest.json', 'backend/uploads/image_processing/outputs/7/compliance_audit.json']);
  }

  // 13 test and result evidence
  { const s=p.slides.add(); s.background.fill=A.ink; title(s,13,'Verification evidence and engineering quality','Tests exercise the isolated backend, image parser, frontend behavior, and critical browser journeys');
    const checks=[['Backend','pytest','93 passed','Temporary SQLite database and uploads'],['Image parsing','pytest','40 passed','Pipeline, geometry, row assignment'],['Frontend','Vitest + TypeScript','22 passed','UI states and report calculations'],['End-to-end','Playwright','2 passed','Analysis product-match journey']];
    checks.forEach((c,i)=>{const y=205+i*82; box(s,70,y,1080,61,'#151a23',14,A.line); txt(s,c[0],95,y+18,150,20,18,[A.teal,A.cyan,A.orange,A.green][i],{bold:true}); txt(s,c[1],285,y+18,190,20,15,A.muted); txt(s,c[2],512,y+14,160,30,23,A.white,{bold:true}); txt(s,c[3],730,y+18,380,20,15,A.pale);});
    box(s,70,555,1080,65,'#211b17',14,'#594319'); txt(s,'What these results do not prove',95,574,245,20,16,A.orange,{bold:true}); txt(s,'They confirm implemented behavior and regressions, not field accuracy, mAP, precision/recall, retail generalization, or OCR accuracy.',360,568,750,34,16,A.white);
    footer(s,13); note(s,['docs/shared/CONTRIBUTIONS.md entries dated 2026-10-22 and 2026-10-23', 'backend/tests/', 'image-parsing/tests/', 'frontend/tests/', 'e2e/tests/analysis_product_match.spec.ts']);
  }

  // 14 journey / decisions
  { const s=p.slides.add(); s.background.fill=A.ink; title(s,14,'Key technical decisions and lessons','The project moved from layout design toward an evidence-conservative photo-to-planogram audit');
    const y=[214,306,398,490]; const dec=[
      ['Physical centimetres instead of pixels','Allows layout rules, exports, and compliance positions to use a common real-world coordinate system.'],
      ['Immutable audit snapshot','Prevents a later planogram edit from rewriting the expected state of an already processed shelf photo.'],
      ['Shelf-scoped candidates before CLIP matching','Reduces irrelevant lookalike candidates and preserves the job’s relevant product catalogue.'],
      ['Conservative compliance outcomes','Uncalibrated position or weak identity evidence becomes review-needed, not a fabricated shortage or exact-SKU claim.']
    ];
    dec.forEach((d,i)=>{box(s,70,y[i],1070,68,'#151a23',14,A.line); box(s,88,y[i]+13,42,42,['#173a39','#112c3a','#332b18','#342129'][i],12); txt(s,String(i+1),88,y[i]+22,42,18,16,[A.green,A.cyan,A.orange,A.rose][i],{bold:true,align:'center'}); txt(s,d[0],154,y[i]+13,420,22,18,A.white,{bold:true}); txt(s,d[1],154,y[i]+38,920,22,14,A.pale);});
    footer(s,14); note(s,['docs/shared/ARCHITECTURE.md', 'docs/shared/COMPLIANCE_ROADMAP.md', 'docs/shared/CONTRIBUTIONS.md']);
  }

  // 15 limitations
  { const s=p.slides.add(); s.background.fill=A.ink; title(s,15,'Current limitations and risks','The prototype intentionally keeps uncertain evidence visible instead of overstating capability');
    const left=[['Model quality','No labelled real-shelf benchmark provides precision, recall, mAP, or SKU accuracy.'],['Matching thresholds','CLIP threshold and ambiguity margin are fixture-informed but not calibrated across product categories.'],['Geometry','Perspective handling supports optional ArUco calibration; physical repeatability remains unmeasured.']];
    const right=[['Catalogue variants','Packshot embeddings and color gates can confuse visually similar packs and seasonal changes.'],['OCR','Live smoke test exists, but no labelled price-tag data supports accuracy claims.'],['Operational readiness','Local SQLite, disk storage, and model dependencies suit prototype use rather than production scale.']];
    [left,right].forEach((arr,col)=>arr.forEach((d,i)=>{const x=col?660:70; const y=205+i*126; box(s,x,y,550,96,'#17181f',16,col?'#513440':'#40351f'); txt(s,d[0],x+24,y+18,460,22,18,col?A.rose:A.orange,{bold:true}); txt(s,d[1],x+24,y+48,490,32,15,A.pale);}));
    footer(s,15); note(s,['docs/shared/COMPLIANCE_ROADMAP.md', 'backend/PRICE_TAG_DETECTION_SETUP.md', 'image-parsing/tests/fixtures/compliance/pipeline-verification/manifest.json']);
  }

  // 16 roadmap
  { const s=p.slides.add(); s.background.fill=A.ink; title(s,16,'Future work and mentor discussion','The highest-value next step is measurable validation on a controlled physical shelf');
    const stages=[['1. Build labelled fixture','Measured shelf rows, pixel boxes, exact SKU/variant identities, price labels, and multiple controlled error scenarios.'],['2. Calibrate decisions','Measure detector quality, matching accuracy, position tolerance, empty-space recall, and OCR correctness.'],['3. Strengthen recognition','Expand catalogue packshots, add variant-specific data, hard-negative examples, and human review feedback.'],['4. Productize','Move beyond local storage, define monitoring, access controls, deployment, and retailer workflow integration.']];
    stages.forEach((d,i)=>{const x=58+i*295; box(s,x,240,258,262,'#151a23',18,A.line); box(s,x+24,267,45,45,['#173a39','#112c3a','#332b18','#342129'][i],22); txt(s,String(i+1),x+24,280,45,20,16,[A.green,A.cyan,A.orange,A.rose][i],{bold:true,align:'center'}); txt(s,d[0],x+24,338,210,48,20,A.white,{bold:true}); txt(s,d[0].startsWith('1')?d[1]:d[1],x+24,404,207,72,15,A.pale);});
    box(s,160,565,960,57,'#173a39',14,'#2c655a'); txt(s,'Mentor prompt: validate the controlled fixture design and success metrics before expanding model complexity.',188,583,905,22,17,A.green,{bold:true,align:'center'});
    footer(s,16); note(s,['docs/shared/COMPLIANCE_ROADMAP.md controlled test fixture checklist', 'docs/shared/PRODUCT_SPEC.md']);
  }

  for (const [i, slide] of p.slides.items.entries()) await writeBlob(path.join(outDir, `slide-${String(i+1).padStart(2,'0')}.png`), await slide.export({format:'png',scale:1}));
  await (await PresentationFile.exportPptx(p)).save(candidatePath);

  const { finalizePresentation } = await import(pathToFileURL(path.join(skillDir,'container_tools/artifact_tool_utils.mjs')).href);
  await finalizePresentation({
    workspaceDir, candidatePath, finalPath, pythonExecutable:runtimePython,
    integrityValidatorPath:path.join(skillDir,'container_tools/inspect_presentation_package_integrity.py'),
    layoutValidatorPath:path.join(skillDir,'container_tools/inspect_presentation_layout_geometry.py'),
    layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit'],
    explicitTotalSlideCount:16,
    fontPolicy:{basis:'design',families:[FONT]}, verifyArtifactToolImport:true,
    receiptPath:path.join(buildDir,'validation-v2.json')
  });
  console.log(JSON.stringify({candidatePath,finalPath,renderDir:outDir,slides:p.slides.items.length}));
}
main().catch(e=>{console.error(e); process.exitCode=1;});
