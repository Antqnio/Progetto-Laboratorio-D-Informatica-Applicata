"use strict";

/**
 * Change the form fields based on the selected configuration file.
 * @param {Event} e - The change event from the select element.
 * This function fetches the JSON file corresponding to the selected configuration name,
 * validates the file name, and updates the form fields with the data from the JSON file.
 * It also checks that the file name contains only valid characters (letters, numbers, and underscores
 */
async function changeFormFields(e) {
    const fileName = e.target.value;
    if (!fileName) return;

    // Check if the file name is valid
    // Only allow letters, numbers, and underscores in the file name
    const validNamePattern = /^[a-zA-Z0-9_]+$/;
    if (!validNamePattern.test(fileName)) {
        console.warn("Invalid configuration name. Only letters, numbers, and underscores are allowed.");
        alert("Invalid name: use only letters, numbers, or underscores (no spaces).");
        return;
    }
    
    // Fetch the JSON file corresponding to the selected configuration name
    try {
        const response = await fetch("/get_json_file?file=" + encodeURIComponent(fileName));
        if (!response.ok) {
            throw new Error(`Error while trying to load the ${fileName}.json file: ${response.status}`);
        }

        const configData = await response.json();
        console.log("Configuration loaded:", configData);
        // Update the form fields with the data from the JSON file
        // Assuming the form fields have IDs that match the keys in the JSON file
        // This will set the value of each input field to the corresponding value in the JSON file
        for (const key in configData) {
            const input = document.getElementById(key);
            input.value = configData[key];
        }
    } catch (error) {
        console.error("Errore durante il fetch del JSON:", error);
    }
}



/**
 * Handles form submission to a Flask backend using Fetch API.
 * Intercepts the submit event, determines which submit button was pressed,
 * and sends the form data via POST request to the server.
 * Displays a success or error message based on the server response.
 *
 * @async
 * @param {SubmitEvent} e - The form submit event.
 */
async function sendFormDataToFlaskClient(e) {
    // Find the pressed submit button to determine the action
    const submitter = e.submitter || document.activeElement;
    if (!submitter || submitter.name !== "action" || (submitter.value !== "apply" && submitter.value !== "save"))
        return;
    e.preventDefault();

    // Get the form element from the event
    const form = e.target;

    /*
        Create a FormData object from the form.
        This allows us to easily send the form data as key-value pairs (key).
        name attribute of each input field in the form will be used as the key,
        and the value of the input field will be used as the value.
    */
    const formData = new FormData(form);
    
    /* 
        Add the action to the form data based on which button was pressed
        This will be used by the Flask backend to determine the action to take
        "apply" will apply the configuration without saving it,
        "save" will save the configuration to a file.
    */
    formData.set("action", submitter.value);
    
    /*
        Send the form data to the Flask backend using Fetch API.
        The server will handle the request and return a response.
        If the response is OK, we will display a success message.
        If the response is not OK, we will display an error message.
    */
    try {
        const response = await fetch("/", {
            method: "POST",
            body: formData
        });
        if (response.ok) {
            const data = await response.json();
        
            // Display a success message based on the action taken
            // If the action is "save", we display a success message for saving the configuration
            // If the action is "apply", we display a success message for applying the configuration
            const p = document.getElementById("message");
            p.textContent = data.message || (submitter.value === "save" ? "Configuration saved!" : "Configuration applied!");
            p.style.display = "block";
            // Hide the message after 3 seconds
            setTimeout(() => {
                p.style.display = "none";
            }, 3000);
            // If the action was "save", we also reload the configuration names
            if (submitter.value === "save") {
                // Get the select element for configuration names
                const configNameSelect = document.getElementById("config_name_select");
                if (configNameSelect) {
                    // Add the new option with the saved configuration name
                    const option = document.createElement("option");
                    // To get the saved configuration name, we have to used the name attribute of the input field
                    // that was used to save the configuration.
                    const configName = formData.get("config_name_text");
                    option.value = configName; // Assuming the server returns the saved file name
                    option.textContent = configName;
                    // Order the options alphabetically
                    for (let child = configNameSelect.firstChild; child; child = child.nextSibling) {
                        if (child.value > configName) {
                            configNameSelect.insertBefore(option, child);
                            return;
                        }
                    }
                }
            }
            
        } else {
            // If the response is not OK, we display an error message
            const data = await response.json();
            const p = document.getElementById("message");
            p.textContent = data.error || "Error while applying the configuration.";
            p.style.display = "block";
            // Hide the error message after 3 seconds
            setTimeout(() => {
                p.style.display = "none";
            }, 3000);
        }
    } catch (err) {
        alert("Network error.");
    }
};

/**
 * Starts the recognition process by sending a request to the server and updating the UI accordingly.
 *
 * @async
 * @param {HTMLButtonElement} startBtn - The button element to start recognition.
 * @param {HTMLButtonElement} stopBtn - The button element to stop recognition.
 * @param {HTMLElement} statusElem - The element displaying the recognition status.
 * @param {HTMLVideoElement} videoElem - The video element to display the video feed.
 * @param {HTMLButtonElement} applyBtn - The button element to apply changes, disabled during recognition.
 * @param {HTMLButtonElement} saveBtn - The button element to save results, disabled during recognition.
 * @returns {Promise<void>} Resolves when the recognition process has started and the UI is updated.
 */
async function startRecognition(startBtn, stopBtn, statusElem, videoElem, applyBtn, saveBtn) {
    const resp = await fetch("/start");
    console.log("Response status:", resp.status, resp.statusText)
    if (resp.ok) {
        // Update the UI to reflect that recognition has started
        statusElem.textContent = "🟢 Active";
        statusElem.style.color = "green";
        startBtn.style.display = "none";
        stopBtn.style.display = "inline-block";
        videoElem.style.display = "block";

        // This line sets the source of the video element to the video feed URL.
        // Everytime videElem.src is changed (it happens everytime the startRecognition is called,
        // and only when the startRecognition is called),
        // the browser will send a GET request to the flask client
        // to the /video_feed endpoint to fetch the live video stream.
        // The ?ts=Date.now() part is used to prevent caching issues, ensuring the
        // browser always fetches the latest video feed.
        // The video element will display the live video feed from the server.
        videoElem.src = "/video_feed?ts=" + Date.now();
        applyBtn.disabled = true;
        saveBtn.disabled = true;
    }
}

/**
 * Stops the recognition process by sending a request to the server and updates the UI accordingly.
 *
 * @async
 * @function stopRecognition
 * @param {HTMLButtonElement} startBtn - The button to start recognition, which will be shown after stopping.
 * @param {HTMLButtonElement} stopBtn - The button to stop recognition, which will be hidden after stopping.
 * @param {HTMLElement} statusElem - The element displaying the current status, which will be updated.
 * @param {HTMLVideoElement} videoElem - The video element displaying the recognition stream, which will be hidden and cleared.
 * @param {HTMLButtonElement} applyBtn - The button to apply changes, which will be enabled after stopping.
 * @param {HTMLButtonElement} saveBtn - The button to save changes, which will be enabled after stopping.
 * @returns {Promise<void>} Resolves when the recognition has been stopped and the UI updated.
 */
async function stopRecognition(startBtn, stopBtn, statusElem, videoElem, applyBtn, saveBtn) {
    const resp = await fetch("/stop");
    console.log("Response status:", resp.status, resp.statusText);
    if (resp.ok) {
        // Update the UI to reflect that recognition has stopped
        statusElem.textContent = "🔴 Inactive";
        statusElem.style.color = "red";
        stopBtn.style.display = "none";
        startBtn.style.display = "inline-block";
        videoElem.style.display = "none";
        videoElem.src = "";
        applyBtn.disabled = false;
        saveBtn.disabled = false;

    }
}


/**
 * Handles the stop client action by preventing the default event behavior,
 * sending a request to the server to stop the client, and reloading the page
 * if the operation is successful. Logs errors to the console if the request fails.
 *
 * @async
 * @param {Event} e - The event object triggered by the user action.
 * @throws {Error} If the fetch request fails.
 * @returns {Promise<void>}
 */
async function stopClient(e) {
    e.preventDefault();  // <- block any submit/navigation
    // Send a request to stop the client
    try {
        const resp = await fetch("/stop_client");
        if (resp.ok) {
            console.log("Client stopped successfully.");
            window.location.reload();  // Reload the page to reflect the changes
        } else {
            console.error("Error stopping the client:", resp.statusText);
        }
    }
    catch (err) {
        console.error("Network error while trying to stop the client:", err)

    }
}

const SERVER_UNREACHABLE = "Server is not running or not reachable.";
let SERVER_CHECK_TIMER = null;
/**
 * Asynchronously checks if the server is running by sending a request to the "/check_server" endpoint.
 * Updates the text content of the element with id "message" based on the server's status.
 * Logs relevant information or errors to the console.
 *
 * @async
 * @function
 * @throws {Error} If the fetch request fails
 * @returns {Promise<void>} Resolves when the server status check is complete and the message is updated.
 */
async function checkIfServerIsRunning() {
    const message = document.getElementById("message");
    if (!message) {
        console.error("Message element not found.");
        return;
    }
    try {
        const resp = await fetch("/check_server");
        if (resp.ok) {  
            console.log("Server is running.");
            message.textContent = "Server is running.";
            clearInterval(SERVER_CHECK_TIMER);  // Stop checking if the server is running
            SERVER_CHECK_TIMER = null;  // Clear the timer variable
        }
        else {
            console.error("Server is not running or not reachable.");
            message.textContent = SERVER_UNREACHABLE
        }
    } catch (err) {
        console.error("Network error while checking server status:", err);
        message.textContent = "Network error while checking server status.";
    }
}

    
/**
 * Initializes event listeners and UI logic for the configuration form and webcam recognition controls.
 *
 * - Sets up change event for configuration selection dropdown.
 * - Handles form submission for "apply" and "save" actions, sending data via fetch and displaying messages.
 * - Manages start/stop recognition buttons, updates UI status, and toggles webcam video feed.
 * - Disables/enables form buttons based on recognition state.
 *
 * Assumes the presence of specific DOM elements with IDs:
 * - config_name_select
 * - configForm
 * - message
 * - recognition-status
 * - start-recognition-btn
 * - stop-recognition-btn
 * - webcam-frame
 * - apply-btn
 * - save-btn
 */
function init() {
    // Add event listener for configuration name selection
    // This will trigger the changeFormFields function when the selected configuration changes
    const config_name_select = document.getElementById('config_name_select');
    if (config_name_select) {
        config_name_select.addEventListener('change', changeFormFields);
    }

    // Add event listener for form submission
    const form = document.getElementById("configForm");
    if (form) {
        form.addEventListener("submit", sendFormDataToFlaskClient)
    }

    /*
        Initialize the recognition status and buttons.
        This will set up the event listeners for the start and stop buttons,
        and update the status text based on the recognition state.
        It will also handle the webcam video feed.
    */

    // Get the elements for recognition status and buttons
    const statusElem = document.getElementById("recognition-status");
    const startBtn = document.getElementById("start-recognition-btn");
    const stopBtn = document.getElementById("stop-recognition-btn");
    const videoElem = document.getElementById("webcam-frame");
    const applyBtn = document.getElementById("apply-btn");
    const saveBtn = document.getElementById("save-btn");

    if (statusElem && startBtn && stopBtn && videoElem && applyBtn && saveBtn) {
        startBtn.addEventListener("click", async (e) => {
            e.preventDefault();  // <- block any submit/navigation
            // Start the recognition process
            await startRecognition(startBtn, stopBtn, statusElem, videoElem, applyBtn, saveBtn);
        });
        
        stopBtn.addEventListener("click", async (e) => {
            e.preventDefault();  // <- block any submit/navigation
            // Stop the recognition process
            await stopRecognition(startBtn, stopBtn, statusElem, videoElem, applyBtn, saveBtn);
        });
    }

    const stopClientBtn = document.getElementById("stop-client-btn");
    if (stopClientBtn) {
        stopClientBtn.addEventListener("click", stopClient);
    }

    const serverMessage = document.getElementById("server-message");
    // Set the initial message for the server status
    serverMessage.textContent = SERVER_UNREACHABLE;
    // Check if the server is running when the page loads
    SERVER_CHECK_TIMER = setInterval(() => {
        // Check if the server is running every 5 seconds
        checkIfServerIsRunning();
    }, 5000);

}

// Wait for the DOM to be fully loaded before initializing
document.addEventListener('DOMContentLoaded', init);