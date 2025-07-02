"use strict";


async function changeFormFields(e) {
    const fileName = e.target.value;
    if (!fileName) return;

    // Controllo: solo lettere, numeri e underscore, senza spazi
    const validNamePattern = /^[a-zA-Z0-9_]+$/;
    if (!validNamePattern.test(fileName)) {
        console.warn("Invalid configuration name. Only letters, numbers, and underscores are allowed.");
        alert("Invalid name: use only letters, numbers, or underscores (no spaces).");
        return;
    }


    const path = `static/configs/${fileName}.json`;
    console.log("Caricamento configurazione da:", path);
    try {
        const response = await fetch(path);
        if (!response.ok) {
            throw new Error(`Errore nel caricamento del file: ${response.status}`);
        }

        const configData = await response.json();
        console.log("Configurazione caricata:", configData);
        for (const key in configData) {
            const input = document.getElementById(key);
            input.value = configData[key];
        }
    } catch (error) {
        console.error("Errore durante il fetch del JSON:", error);
    }
}

function init() {
    const config_name_select = document.getElementById('config_name_select');
    if (config_name_select) {
        config_name_select.addEventListener('change', changeFormFields);
    }

    // Intercetta il submit del form per "apply"
    const form = document.getElementById("configForm");
    if (form) {
        form.addEventListener("submit", async function(e) {
            // Trova il bottone premuto
            const submitter = e.submitter || document.activeElement;
            if (!submitter || submitter.name !== "action" || (submitter.value !== "apply" && submitter.value !== "save"))
                return;
            e.preventDefault();

            const formData = new FormData(form);
            formData.set("action", submitter.value);

            try {
                const response = await fetch("/", {
                    method: "POST",
                    body: formData
                });
                if (response.ok) {
                    const data = await response.json();
                    //alert(data.message || (submitter.value === "save" ? "Configurazione salvata!" : "Configurazione applicata!"));
                    const p = document.getElementById("message");
                    p.textContent = data.message || (submitter.value === "save" ? "Configurazione salvata!" : "Configurazione applicata!");
                    p.style.display = "block";
                    setTimeout(() => {
                        p.style.display = "none";
                    }, 3000); // Nasconde il messaggio dopo 3 secondi
                } else {
                    const data = await response.json();
                    const p = document.getElementById("message");
                    p.textContent = data.error || "Errore nell'applicazione della configurazione.";
                    p.style.display = "block";
                    setTimeout(() => {
                        p.style.display = "none";
                    }, 3000); // Nasconde il messaggio dopo 3 secondi
                }
            } catch (err) {
                alert("Errore di rete.");
            }
        });


    
    }

    const statusElem = document.getElementById("recognition-status");
    const startBtn = document.getElementById("start-recognition-btn");
    const stopBtn = document.getElementById("stop-recognition-btn");
    const videoElem = document.getElementById("webcam-frame"); // Assicurati che l'img abbia questo id
    const applyBtn = document.getElementById("apply-btn");
    const saveBtn = document.getElementById("save-btn");
    console.log("stopBtn", stopBtn);
    if (startBtn && stopBtn && videoElem) {
        startBtn.addEventListener("click", async function(e) {
            e.preventDefault();  // <- blocca qualsiasi submit/navigation
            const resp = await fetch("/start");
            if (resp.ok) {
                console.log("sono qui verde")
                statusElem.textContent = "🟢 Active";
                statusElem.style.color = "green";
                startBtn.style.display = "none";stopBtn.style.display = "inline-block";
                videoElem.style.display = "block";
                videoElem.src = "/video_feed?ts=" + Date.now();
                applyBtn.disabled = true;
                saveBtn.disabled = true;
                console.log("apply-btn ", applyBtn);
            }
        });
        
        console.log("Inizializzazione del bottone di stop");
        stopBtn.addEventListener("click", async function(e) {
            e.preventDefault();  // <- blocca qualsiasi submit/navigation
            const resp = await fetch("/stop");
            console.log("Response status:", resp.status, resp.statusText);
            if (resp.ok) {
                statusElem.textContent = "🔴 Inactive";
                statusElem.style.color = "red";
                stopBtn.style.display = "none";
                startBtn.style.display = "inline-block";
                videoElem.style.display = "none";
                videoElem.src = "";
                applyBtn.disabled = false;
                saveBtn.disabled = false;

            }
        });
    }

}

document.addEventListener('DOMContentLoaded', init);