const uploadInput = document.getElementById("uploadInput");
const btnRecognize = document.getElementById("btnRecognize");

const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const btnStartCam = document.getElementById("btnStartCam");
const btnSnap = document.getElementById("btnSnap");
const btnRecognizeCam = document.getElementById("btnRecognizeCam");

const statusEl = document.getElementById("status");
const resultName = document.getElementById("resultName");
const preview = document.getElementById("preview");

const personName = document.getElementById("personName");
const personImage = document.getElementById("personImage");
const btnAdd = document.getElementById("btnAdd");
const peopleList = document.getElementById("peopleList");

let stream = null;
let capturedBlob = null;

function setStatus(msg){ statusEl.textContent = "Status: " + msg; }

function renderPeople(list){
  peopleList.innerHTML = "";
  list.forEach(p=>{
    const li = document.createElement("li");
    li.textContent = p;
    peopleList.appendChild(li);
  });
}
renderPeople(initialPeople || []);

async function recognizeFile(file){
  if(!file){ alert("Choose an image first."); return; }
  setStatus("recognizing...");
  const fd = new FormData();
  fd.append("image", file);

  const res = await fetch("/recognize", { method:"POST", body: fd });
  const data = await res.json();

  if(!data.ok){ setStatus("error"); alert(data.error); return; }

  resultName.textContent = data.name;
  preview.src = data.file;
  preview.style.display = "block";
  setStatus("done");
}

btnRecognize.addEventListener("click", ()=>{
  recognizeFile(uploadInput.files[0]);
});

btnStartCam.addEventListener("click", async ()=>{
  try{
    stream = await navigator.mediaDevices.getUserMedia({ video:true, audio:false });
    video.srcObject = stream;
    setStatus("camera opened");
  }catch(e){
    alert("Camera error: " + e.message);
  }
});

btnSnap.addEventListener("click", ()=>{
  if(!stream){ alert("Open camera first"); return; }
  const w = video.videoWidth;
  const h = video.videoHeight;
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0, w, h);

  canvas.toBlob((blob)=>{
    capturedBlob = blob;
    preview.src = URL.createObjectURL(blob);
    preview.style.display = "block";
    setStatus("captured");
  }, "image/jpeg", 0.95);
});

btnRecognizeCam.addEventListener("click", async ()=>{
  if(!capturedBlob){ alert("Capture first"); return; }
  const file = new File([capturedBlob], "capture.jpg", { type:"image/jpeg" });
  recognizeFile(file);
});

btnAdd.addEventListener("click", async ()=>{
  const name = personName.value.trim();
  const imgFile = personImage.files[0];

  if(!name) return alert("Enter a name");
  if(!imgFile) return alert("Choose an image");

  setStatus("adding person...");
  const fd = new FormData();
  fd.append("name", name);
  fd.append("image", imgFile);

  const res = await fetch("/add_person", { method:"POST", body: fd });
  const data = await res.json();

  if(!data.ok){ setStatus("error"); return alert(data.error); }

  alert(data.message);
  renderPeople(data.people);
  personName.value = "";
  personImage.value = "";
  setStatus("ready");
});
