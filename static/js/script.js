"use strict";


async function changeFormFields(e) {
    const fileName = e.target.value;
    if (!fileName) return;

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

}

document.addEventListener('DOMContentLoaded', init);