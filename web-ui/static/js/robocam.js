const button = document.querySelector('.waypointtoggle');
const close_button = document.querySelector('#waypoint-view-close');
const pane = document.querySelector('.waypointpane');

button.addEventListener('click', () => {
    pane.classList.toggle('open');
});
close_button.addEventListener('click', () => {
    pane.classList.toggle('open');
});

const tl_button = document.querySelector('.timelapsetoggle');
const tl_close_button = document.querySelector('#timelapse-view-close');
const tl_pane = document.querySelector('.timelapsepane');

tl_button.addEventListener('click', () => {
    tl_pane.classList.toggle('open');
});
tl_close_button.addEventListener('click', () => {
    tl_pane.classList.toggle('open');
});

const al_button = document.querySelector('.limitstoggle');
const al_close_button = document.querySelector('#limits-view-close');
const al_pane = document.querySelector('.limitspane');

al_button.addEventListener('click', () => {
    al_pane.classList.toggle('open');
});
al_close_button.addEventListener('click', () => {
    al_pane.classList.toggle('open');
});
(async function polling(){
    
    const response = await fetch('/refresh/status', {
        method: 'post',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({"refresh": "status"})
    });
    response.json().then(data =>{
        console.log(data); // JSON data parsed by `data.json()` call
        update_status(data);
    });
    
    
                            
    // periodically refresh
    setTimeout(polling, 30000);
})();
async function update_status(status){
    var element = document.getElementById("status-text");  
    
    state = status.status;
    update_time = status.last_update;
    work_position = status.work_pos;
    machine_position = status.machine_pos;
    element.innerHTML = "Status:<b>"+state + "</b> Updated:<b>"+update_time+"</b></br>Work position:"+work_position+"</br>Machine position:"+machine_position;
}
async function update_waypoints(wp){
    var tbodyRef = document.getElementById('waypoint-table').getElementsByTagName('tbody')[0];
    $("#waypoint-table tbody tr").remove(); 
    wp.forEach(w => {
        // Insert a row at the end of table
        var newRow = tbodyRef.insertRow();
        
        // Insert a cell at the end of the row
        var id_cell = newRow.insertCell();
        id_cell.innerHTML = w['id']+"up/down"
        
        var loc_cell = newRow.insertCell();
        loc_cell.innerHTML ="x"+w['x']+",y"+w['y']+",z"+w['z']+",a"+w['a']+",b"+w['b']+"<br/>"+ w['travel_duration']+"sec ;"+ w['feed']+"mm/s ; dwell : "+ w['dwell_time'] 

        var action_cell = newRow.insertCell();
        action_cell.innerHTML = 'Edit/<input type = "button" class="myButton" id = "move_to_waypoint_'+ w['id'] +'" value = "Move" onclick="move_to_waypoint('+ w['id']+')"/><br/><input type = "button" class="myButton" id = "delete_waypoint_'+ w['id'] +'" value = "X" onclick="delete_waypoint('+ w['id']+')"/>'
    });
    
}
async function save_savepoint(id) { 
    const response = fetch('/save_savepoint', {
        method: 'post',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            "savepoint_id": id
        })
    });
    console.log('Completed!', response);
}; 
async function add_waypoint(){
    var value = document.getElementById("dwell-time").value;
    response = post_command('/add_waypoint',JSON.stringify({"waypoint": "add","dwell_time":value}));
    response.then(data =>{
        console.log(data); // JSON data parsed by `data.json()` call
        update_waypoints(data);
    });
    
}
async function move_to_savepoint(id) { 
    const response = fetch('/move_to_savepoint', {
        method: 'post',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            "savepoint_id": id
        })
    });
    console.log('Completed!', response);
};
async function move_to_waypoint(id) { 
    response = post_command('/move_to_waypoint',JSON.stringify({"waypoint_id": id}));
    console.log('way point move', response);
};
async function delete_waypoint(id) { 
    response = post_command('/delete_waypoint',JSON.stringify({"waypoint_id": id}));
    console.log('way point delete', response);
    response.then(data =>{
        console.log(data); // JSON data parsed by `data.json()` call
        update_waypoints(data);
    });
};

async function start_timelapse(){
    var tl_duration = document.getElementById("tl-duration").value;
    var tl_steptime = document.getElementById("tl-steptime").value;
    response = post_command('/timelapse_start',JSON.stringify({"timelapse": "start","duration":tl_duration,"step-interval":tl_steptime}));
}

async function reset_limits(){
    response = post_command('/reset/limits',JSON.stringify({"limits": "reset"}));
}


async function showHideForm(box, id,id_2) {
    var elm = document.getElementById(id);
    var secondelem = document.getElementById(id_2);
    if(box.checked){
        elm.style.display = "none";
        secondelem.style.display ="";
    } else {
        elm.style.display = "";
        secondelem.style.display ="none";
    }
}
async function toggle_flip(cb){
    console.log(cb)
    var idAttr = $(cb).prop('id');
    console.log(idAttr +" toggled  "+cb.checked)
    
    response = post_command('/toggle/'+idAttr, '{"state": '+cb.checked+'}')
    response.then(data =>{
        console.log(data); // JSON data parsed by `data.json()` call
        cb.checked = data.result;
    });
}
async function drop_down_select(elem_id){
    var value = document.getElementById(elem_id).value;
    if (isNaN(value)){
    payload = '{"'+elem_id+'":"'+value+'"}'
    }else{
    payload = '{"'+elem_id+'":'+value+'}'
    }
    post_command('/update/'+elem_id, payload);
}
async function post_command(url,payload){
    const response = await fetch(url, {
        method: 'post',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: payload
    });
    return response.json()
}

