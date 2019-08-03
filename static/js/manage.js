function mem_html(id, name) {
    var mem = document.createElement('div');
    mem.innerHTML ='<a href="#!" id="' + id + '" class="list-group-item list-group-item-action">' + name + '</a>';
    return mem;
  }

var mem_list;
var new_id = 0;
function update_members(){
    document.getElementById('members').innerHTML = "";
    fetch('./get-list').then(response => {
        return response.json();
    }).then(data => {
        mem_list = data;
        new_id = 1023;
        data.forEach(element => {
        if(element["id"] > new_id){
            new_id = element["id"]
        }
        document.getElementById('members').appendChild(mem_html(element["id"], element["name"]));
        });
        document.getElementById('members').appendChild(mem_html("add_new", "Add New +"));
        if(update_view)
        click_event_custom(document.getElementById("id").value);

    }).catch(err => {
        console.log(err);
    });
}

$(document).ready(function() {
    enable_all(true);
    update_view = false;
    file_selected= false;
    update_members();
});


function enable_all(s){
    document.getElementById("name").disabled=s;
    document.getElementById("email").disabled=s;
    document.getElementById("phone").disabled=s;
    document.getElementById("auth").disabled=s;
}


function click_event(event) {
    enable_all(false);
    console.log( event.target.id );
    document.getElementById("file").disabled=false;
    if(event.target.id == "add_new") {
        document.getElementById("id").value=new_id+1;
        $('#id').change();
        document.getElementById("name").value="";
        $('#name').change();
        document.getElementById("phone").value="";
        $('#phone').change();
        document.getElementById("email").value= "";
        $('#email').change();
        document.getElementById("auth").checked = false;
        $('#auth').change();
        document.getElementById("img").src = "";
        document.getElementById("update_btn").innerText = "Add";
        document.getElementById("update_btn").disabled = false;
        document.getElementById("delete_btn").style.display = "none";

    } else {
        document.getElementById("update_btn").innerText = "Update";
        document.getElementById("delete_btn").style.display = "block";
        document.getElementById("update_btn").disabled = true;
        mem_list.forEach(element => {
            if(element["id"] == event.target.id){
                set_current_panal(element);
            }
        });
    }
}

function click_event_custom(id) {
    enable_all(false);
    document.getElementById("file").disabled=false;
        document.getElementById("update_btn").innerText = "Update";
        document.getElementById("delete_btn").style.display = "block";
        document.getElementById("update_btn").disabled = true;
        mem_list.forEach(element => {
            if(element["id"] == id){
                set_current_panal(element);
            }
        });
    
}


$("#members").on("click", function(event){
    click_event(event);
});

var current_element;
function set_current_panal(element) {
    current_element = element;
    document.getElementById("id").value=element.id;
    $('#id').change();
    document.getElementById("name").value=element.name;
    $('#name').change();
    document.getElementById("phone").value=element.phone;
    $('#phone').change();
    document.getElementById("email").value=element.email;
    $('#email').change();
    document.getElementById("img").src= "./profile/" + element.img;
    if (element.auth == "True") {
        state = true
    } else {
        state = false
    }
    document.getElementById("auth").checked = state;
}

var file_selected;
function refrm() {
    if(current_element != undefined) {
    if (current_element.auth == "True") {
        state = true
    } else {
        state = false
    }
    if(document.getElementById("id").value == current_element.id && document.getElementById("name").value == current_element.name && document.getElementById("phone").value == current_element.phone && document.getElementById("email").value == current_element.email && document.getElementById("auth").checked == state && file_selected == false){
        document.getElementById("update_btn").disabled = true;
    } else {
        document.getElementById("update_btn").disabled = false;
    }
}
}

$( "#update_btn" ).click(function(event) {
    event.preventDefault(); 
    if(file_selected == false) {
        if(document.getElementById("update_btn").innerText.toLowerCase() == "update"){
            upload_details("same_image");
        } else {
            upload_img();
        }
    } else {
        upload_img();
    }
});

function upload_details(img_url) {
    var url;
    if(document.getElementById("update_btn").innerText.toLowerCase() == "update"){
        url = "/update";
    } else {
         url = "/register";
    }
    if (document.getElementById("auth").checked == true) {
        state = "True"
    } else {
        state = "False"
    }
    document.getElementById("update_btn").innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true">';
    document.getElementById("update_btn").disabled = true;
    $.post( url, {
        img: img_url,
        id: document.getElementById("id").value ,
        name: document.getElementById("name").value,
        phone: document.getElementById("phone").value,
        email: document.getElementById("email").value,
        auth: state
    }).then(function(resp) {
        document.getElementById("update_btn").innerHTML = 'Update';
        document.getElementById("update_btn").disabled = false;
        update_view = (document.getElementById("update_btn").innerText.toLowerCase() != "update");
        update_members();
        return false;
    }).catch(function(e) {
        console.log(e);
    });

}

document.getElementById("file").onchange = e => { 
    var file = e.target.files[0];
    file_selected = true;
    console.log(file_selected);
    if(file != undefined) {
        var reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = readerEvent => {
            var content = readerEvent.target.result; 
            document.getElementById("img").src = content;
        }
        refrm();
    }
 }

function upload_img(){
    var fd = new FormData();
    var files = $('#file')[0].files[0];
    fd.append('file',files);
    $.ajax({
        url: './upload',
        type: 'post',
        data: fd,
        contentType: false,
        processData: false,
        success: function(response){
            if(response != "error" && response != 0){
                upload_details(response);
            }else{
                alert("Please select an image");
            }
        },
        error: function(e) 
	    	{
                console.log(e);
                document.getElementById("id").value=new_id+1;
                $('#id').change();
                document.getElementById("name").value="";
                $('#name').change();
                document.getElementById("phone").value="";
                $('#phone').change();
                document.getElementById("email").value= "";
                $('#email').change();
                document.getElementById("auth").checked = false;
                $('#auth').change();
                document.getElementById("img").src = "";
	    	} 	
    });
    return false;
  }

  
$( "#delete_btn" ).click(function(event) {
    event.preventDefault(); 
    delete_mem(current_element.id)
});

  function delete_mem(id) {
    url = "/delete"
    $.post( url, {
        id: id
    }).then(function(resp) {
        current_element = undefined;
        document.getElementById("id").value=new_id+1;
        $('#id').change();
        document.getElementById("name").value="";
        $('#name').change();
        document.getElementById("phone").value="";
        $('#phone').change();
        document.getElementById("email").value= "";
        $('#email').change();
        document.getElementById("auth").checked = false;
        $('#auth').change();
        document.getElementById("img").src = "";
        document.getElementById("delete_btn").style.display = "none";
        update_view = false;
        update_members();
        
    });
  }