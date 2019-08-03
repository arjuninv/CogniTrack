  var config = {
    apiKey: "AIzaSyAS3GgqoiMErYeagXRbWLeFOp5LCelK19A",
    authDomain: "cognitrack-c16c7.firebaseapp.com",
    databaseURL: "https://cognitrack-c16c7.firebaseio.com",
    projectId: "cognitrack-c16c7",
    storageBucket: "cognitrack-c16c7.appspot.com",
    messagingSenderId: "637925214368"
  };
  firebase.initializeApp(config);


  function initMap() {
    var myLatLng = {lat:15.369110, lng:75.121749};

    var map = new google.maps.Map(document.getElementById('map'), mapOptions = {
      zoom: 16,
      center: myLatLng,
      zoomControl: false,
      mapTypeControl: false,
      scaleControl: false,
      streetViewControl: false,
      rotateControl: false,
      fullscreenControl: true
    });

    var marker = new google.maps.Marker({
      position: myLatLng,
      map: map,
      title: 'Camera Location'
    });
  }


  function cam_html(ip) {
    var cam = document.createElement('div');
    cam.innerHTML ='<a href="#!" id="' + ip + '" class="list-group-item list-group-item-action frame"><img src="/thumbnail/' + ip + '/frame.jpg" id=' + ip + ' ></a>';
    return cam;
  }

  var mem_list;


  function mem_html(id, name) {
    var mem = document.createElement('div');
    mem.innerHTML ='<a href="#!" id="' + id + '" class="list-group-item list-group-item-action">' + name + '</a>';
    return mem;
  }

  var camscn = firebase.database().ref('ip_list/');
    camscn.on('value', function(snapshot) {
        document.getElementById('cam_list').innerHTML = "";
        if(snapshot.val() != null && snapshot.val() != ""){
        snapshot.val().split(",").forEach(function(ip) {
            norm_ip = ip.split(".").join("")
            console.log(norm_ip);
            document.getElementById('cam_list').appendChild(cam_html(norm_ip));
            if(norm_ip == "1013155") norm_ip = "19216813760";
            if(norm_ip == "101490") norm_ip = "192168137136"; 
            firebase.database().ref('camera/' + norm_ip + "/blackout/status").on('value', function(snapshot_a) {
              if(snapshot_a.val() == "1"){
                document.getElementById("alert_message").innerText = "Camera ID:" + norm_ip + " is blacked out.";
                document.getElementById('alert').play();
                $('#alertModal').modal("show");

              }
              console.log(snapshot_a.val())
            });
        });
      }
});

function update_members(){
    document.getElementById('members').innerHTML = "";
    fetch('./get-list').then(response => {
        return response.json();
    }).then(data => {
        mem_list = data;
        data.forEach(element => {
        document.getElementById('members').appendChild(mem_html(element["id"], element["name"]));
        });
    }).catch(err => {
        console.log(err);
    });
}

$(document).ready(function() {
    update_members();
    var alerts = firebase.database().ref('alert/');
    alerts.on('value', function(snapshot) {
      console.log(snapshot.val().toString().length);
      if(snapshot.val().toString().length > 5 && snapshot.val().msg != ""){
        console.log("-" + snapshot.val().msg + "-")
      document.getElementById("alert_message").innerText = snapshot.val().msg;
      document.getElementById('alert').play();
      $('#alertModal').modal("show");
      }
    });
});

$("#members").on("click", function(event){
  
  document.getElementById("track_panel").style.display="none"; 

  document.getElementById("cam_panel").style.display="none"; 
  document.getElementById("mem_panel").style.display="block";
  console.log( event.target.id );
  if(mem_scan != undefined) mem_scan.off();
  document.getElementById("frame").src="/stream/" + event.target.id + "/frame.jpg";
  var mem_scan = firebase.database().ref('track/' + event.target.id + '/current_loc/cam');
  mem_scan.on('value', function(snapshot) {
    console.log("snap: " + snapshot.val());

    if(snapshot.val() !=null) {
    document.getElementById("frame").src="/stream/" + snapshot.val().split(".").join("") + "/frame.jpg";
    console.log('camera/' + snapshot.val().split(".").join(""));
    return firebase.database().ref('camera/' + snapshot.val().split(".").join("")).once('value').then(function(snapshot) {
    console.log(snapshot.val()["location"])
    if(snapshot.val()["location"].includes(",")) {
      var LatLng = new google.maps.LatLng(snapshot.val()["location"].split(",")[0], snapshot.val()["location"].split(",")[1]);
      var map = new google.maps.Map(document.getElementById("map"), {
        zoom: 16,
        center: LatLng,
        zoomControl: false,
        mapTypeControl: false,
        scaleControl: false,
        streetViewControl: false,
        rotateControl: false,
        fullscreenControl: true
      });
      var marker = new google.maps.Marker({
          position: LatLng,
          title:"Camera Location"
      });
      marker.setMap(map);
      marker.setPosition(LatLng);
    }
  });
  
    }
  });
  mem_list.forEach(element => {
      if(element["id"] == event.target.id){
          set_current_panal(element);
      }
  });
  
});

function set_current_panal(element) {
  console.log(element);
  document.getElementById("disp-id").innerText=element.id;
  document.getElementById("log").href = "./log/" + event.target.id;

  document.getElementById("disp-name").innerText=element.name;
  document.getElementById("disp-phone").innerText=element.phone;
  document.getElementById("disp-email").innerText=element.email;
  document.getElementById("disp-auth").innerText=element.auth;

}

$("#cam_list").on("click", function(event){
  document.getElementById("track_panel").style.display="block"; 
  document.getElementById("cam_panel").style.display="block"; 
  document.getElementById("mem_panel").style.display="none";
  console.log( event.target.id );
  document.getElementById("c-disp-id").innerText = event.target.id;

  document.getElementById("frame").src="/stream/" + event.target.id + "/frame.jpg";
  console.log('camera/' + event.target.id);
  firebase.database().ref('camera/' + event.target.id).once('value').then(function(snapshot) {

    console.log(snapshot.val());
      document.getElementById("c-disp-loc").innerText = snapshot.val()["location"];
    if(snapshot.val()["location"].includes(",")) {
        var LatLng = new google.maps.LatLng(snapshot.val()["location"].split(",")[0], snapshot.val()["location"].split(",")[1]);
        var map = new google.maps.Map(document.getElementById("map"), {
          zoom: 16,
          center: LatLng,
          zoomControl: false,
          mapTypeControl: false,
          scaleControl: false,
          streetViewControl: false,
          rotateControl: false,
          fullscreenControl: true
        });
        
        var marker = new google.maps.Marker({
            position: LatLng,
            title:"Camera Location"
        });
            marker.setMap(map);


        marker.setPosition(LatLng);
      }

      if(snapshot.val()["location_name"] != null) {
        document.getElementById("c-disp-loc-name").innerText = snapshot.val()["location_name"];
      }
      
    });

    var get_faces = firebase.database().ref('camera_track/' + event.target.id);
    get_faces.on('value', function(snapshot) {
      var flag = 1;
      snapshot.forEach(element => {
        if(flag == 1) {document.getElementById('track_table').innerHTML = ""; flag = 0}
        document.getElementById('track_table').appendChild(face_rec(element.val().time,element.key, element.val().name));
      });
    });
});


 function face_rec(time, id, name) {
    var row = document.createElement('tr');
    row.innerHTML = '<td>' + time + '</td><td>' + id +'</td><td>' + name + '</td>';
    return row;
  }



