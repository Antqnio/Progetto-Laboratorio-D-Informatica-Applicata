"use strict";






async function changeFormFields(e) {
    const fileName = e.target.value;
    const path = `../../app/configs/${fileName}.json`;
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
        // Qui puoi usare configData come oggetto JS
        }
    } catch (error) {
        console.error("Errore durante il fetch del JSON:", error);
    }
}

function init() {
    const config_name_select = document.getElementById('config_name_select');
    config_name_select.addEventListener('change', changeFormFields);
}

document.addEventListener('DOMContentLoaded', init);