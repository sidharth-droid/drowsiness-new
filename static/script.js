const video = document.getElementById("video");
const canvas = document.createElement("canvas");
const ctx = canvas.getContext("2d");
const statusText = document.getElementById("status");
const alarm = document.getElementById("alarm");

navigator.mediaDevices.getUserMedia({ video: true })
  .then(stream => {
    video.srcObject = stream;
    video.play();
    canvas.width = 640;
    canvas.height = 480;

    setInterval(() => {
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      canvas.toBlob(blob => {
        const formData = new FormData();
        formData.append('frame', blob, 'frame.jpg');
        fetch('/detect', { method: 'POST', body: formData })
          .then(res => res.json())
          .then(data => {
            if (data.status === 'drowsy') {
              statusText.innerText = "Status: DROWSY";
              if (alarm.paused) alarm.play();
            } else {
              statusText.innerText = "Status: Awake";
              if (!alarm.paused) {
                alarm.pause();
                alarm.currentTime = 0;
              }
            }
          }).catch(console.error);
      }, 'image/jpeg');
    }, 500);  // send frame every 500ms
  })
  .catch(err => console.error("Camera error:", err));

function enableSound() {
  alarm.play().then(() => {
    alarm.pause();
    alarm.currentTime = 0;
  }).catch(console.log);
}

function stopCamera() {
  // stop webcam stream
  if (video.srcObject) {
    video.srcObject.getTracks().forEach(track => track.stop());
    video.srcObject = null;
    statusText.innerText = "Status: Camera stopped";
  }
  if (!alarm.paused) {
    alarm.pause();
    alarm.currentTime = 0;
  }
}




// const video = document.getElementById("videoFeed");
// const statusText = document.getElementById("status");
// const alarm = document.getElementById("alarm");

// video.src = "/video";

// // Ensure audio will play after user interacts
// document.body.addEventListener("click", () => {
//   alarm.play().then(() => alarm.pause()); // warm-up for autoplay policy
// }, { once: true });

// function pollStatus() {
//   fetch('/status')
//     .then(response => response.json())
//     .then(data => {
//       console.log(data.status)
//       if (data.status === 'drowsy') {
//         statusText.innerText = "Status: DROWSY";
//         // console.log(alarm.paused)
//         if (alarm.paused) {
//           alarm.play().catch(e => console.log("Autoplay blocked", e));
//         }
//       } else {
//         statusText.innerText = "Status: Awake";
//         if (!alarm.paused) {
//           alarm.pause();
//           alarm.currentTime = 0;
//         }
//       }
//     })
//     .catch(error => console.error("Status error:", error));
// }

// setInterval(pollStatus, 500);

// function enableSound() {
//   alarm.play().then(() => {
//     alarm.pause();  // pause immediately so we can control it later
//     alarm.currentTime = 0;
//     console.log("Alarm enabled");
//   }).catch(err => {
//     console.log("User interaction required:", err);
//   });
// }

// function stopCamera() {
//   fetch('/stop', { method: 'POST' })
//     .then(response => response.json())
//     .then(data => {
//       console.log(data.message);
//       document.getElementById("videoFeed").src = "";
//     })
//     .catch(error => console.error("Stop error:", error));
// }

