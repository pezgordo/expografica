document.addEventListener('DOMContentLoaded', (event) => {
  const qrcode = window.qrcode;

  if (!qrcode) {
      console.error("qrcode library not loaded");
      return;
  }

  const video = document.createElement("video");
  const canvasElement = document.getElementById("qr-canvas");
  const canvas = canvasElement.getContext("2d");

  const qrResult = document.getElementById("qr-result");
  const outputData = document.getElementById("outputData");
  const btnScanQR = document.getElementById("btn-scan-qr");

  let scanning = false;

  qrcode.callback = res => {
      if (res) {
          const parsedData = parseVCard(res);
          outputData.innerHTML = parsedData;
          scanning = false;

          video.srcObject.getTracks().forEach(track => {
              track.stop();
          });

          qrResult.hidden = false;
          canvasElement.hidden = true;
          btnScanQR.hidden = false;
      }
  };

  btnScanQR.onclick = () => {
      navigator.mediaDevices
          .getUserMedia({ video: { facingMode: "environment" } })
          .then(function(stream) {
              scanning = true;
              qrResult.hidden = true;
              btnScanQR.hidden = true;
              canvasElement.hidden = false;
              video.setAttribute("playsinline", true); // required to tell iOS safari we don't want fullscreen
              video.srcObject = stream;
              video.play();
              tick();
              scan();
          })
          .catch(err => {
              console.error(err);
          });
  };

  function tick() {
      if (scanning) {
          canvasElement.height = video.videoHeight;
          canvasElement.width = video.videoWidth;
          canvas.drawImage(video, 0, 0, canvasElement.width, canvasElement.height);
          requestAnimationFrame(tick);
      }
  }

  function scan() {
      try {
          qrcode.decode();
      } catch (e) {
          if (scanning) {
              setTimeout(scan, 300);
          }
      }
  }

  function parseVCard(data) {
    const lines = data.split('\n');
    let result = '<ul>';
    const labels = {
        'VERSION': 'Versión',
        'N': 'Nombre',
        'ORG': 'Empresa',
        'ROLE': 'Cargo',
        'TEL': 'Teléfono',
        'EMAIL': 'Correo',
        'NOTE': 'Documento',
        'CATEGORIES': 'Feria',
        'UID': 'Identificador'
    };

    lines.forEach(line => {
        if (line.startsWith('BEGIN:VCARD') || line.startsWith('END:VCARD')) {
            return;
        }
        const parts = line.split(':');
        const key = parts[0].trim();
        const value = parts.slice(1).join(':').trim();
        const label = labels[key] || key; // Use custom label or default key if no custom label exists
        result += `<li><strong>${label}:</strong> ${value}</li>`;
    });
    result += '</ul>';
    return result;
  }
});
