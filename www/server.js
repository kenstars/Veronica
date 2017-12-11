var fs = require("fs");
var config = JSON.parse(fs.readFileSync('../config.json', 'utf8'));
var ui_config = JSON.parse(fs.readFileSync('ui_config.json', 'utf8'));
var gearmanip = config.gearmanip;
var gearmanport = config.gearmanport;
var Gearman = require("node-gearman");
var client = new Gearman(gearmanip, gearmanport);
var dashboard_data_creator = config.dashboard_db_reader;
var serverPort = ui_config.serverport;

client.connect();
console.log("Veronica Socket server started at: ", serverPort);

function createuIdFb(data){
  if(data.channel === 'fb'){
    data.uId = data.session_id;
  }
  return data;
}
var socket_id;
//Socket Handler
io = require('socket.io').listen(serverPort).sockets.on('connection', function (socket)  {
  console.log("listening...");
  socket.auth = false;
  socket.emit('initialvalue',"");
  //check the auth data sent by the client
  socket.on('fetch_weather_details', function(data){
    console.log("in fetch_weather_details", data);
    socket.emit('send_append_data', data);
  });

  socket.on('send_ip_details', function(data){
    console.log("inside server with ip data");
    console.log(JSON.stringify(data));
    socket_id = socket.id;
    // var data = JSON.parse(data);
    // data.socket_id = socket.id;
    //   console.log("data after socket_id");
    console.log(JSON.stringify(data));
    job = client.submitJob("send_location_details",JSON.stringify(data));

    job.on("data", function(data){
    console.log("inside job data"+data.toString("utf-8")); // gnirts tset
    socket.emit("send_append_data", JSON.parse(data));
    });
    job.on("end", function(){
    console.log("job completed"); // gnirts tset
    });
    job.on("error", function(error){
      console.log("inside error");
    console.log(error.message); // gnirts tset
    });
  });

  socket.on('send_newfeed_call', function(data){
    console.log("inside server for newsfeed call");
    console.log(JSON.stringify(data));
    socket_id = socket.id;
    // var data = JSON.parse(data);
    // data.socket_id = socket.id;
    //   console.log("data after socket_id");
    console.log(JSON.stringify(data));
    job = client.submitJob("call_for_newsfeed",JSON.stringify(data));

    job.on("data", function(data){
    console.log("inside newsfeed job data"+data.toString("utf-8")); // gnirts tset
    socket.emit("send_news_feeds", JSON.parse(data));
    });
    job.on("end", function(){
    console.log("job completed"); // gnirts tset
    });
    job.on("error", function(error){
      console.log("inside newsfeed error");
    console.log(error.message); // gnirts tset
    });
  });

  socket.on('receive_data',function(data){
      console.log("in receive_data");
      console.log(data);
      //data = JSON.parse(data);
      if(data.channel === "web"){
          web_socket_id = socket.id;
          console.log(socket.id);
          console.log('web_socket===',web_socket_id);
      } else if(data.channel === "fb"){
          console.log(socket.id);
          console.log("fb web_socket===",data.uId);
          data.session_id = data.uId;
      }

      console.log("---" + JSON.stringify(data));
      data.timestamp = parseInt(new Date().getTime()/1000);
      job = client.submitJob("node_to_chat_tata_move",JSON.stringify(data));

      job.on("data", function(data){
      console.log("Gearman:",data.toString("utf-8")); // gnirts tset
      //socket.emit(data.toString("utf-8"));
      var jsonContent = JSON.parse(data);
      //var chat_worker_response = jsonContent;
      jsonContent = createuIdFb(jsonContent);
      console.log('to resp_message >>> ', jsonContent);
      io.to(socket.id).emit('resp_message', jsonContent);
      });

      job.on("end", function(){
          console.log("Job completed!");
      });

      job.on("error", function(error){
          console.log(error.message);
      });

  });

//   ============= END CHAT FEEDBACK =============

    socket.on('endchatfeedback',function(data){
        console.log("\n End chat feedback===>",data);

        });

    socket.on('tata_move_dashboard_initialized',function(data){
        console.log("received in node", JSON.stringify(data));
        callDashboard(data, socket.id);
  });



  function callDashboard(data, sid){
        console.log("in call Dashboard", data);
        dashboard_job = client.submitJob(dashboard_data_creator, JSON.stringify({}));
        dashboard_job.on("data",function(job){
            dashboard_job.on("end",function(){
              console.log("in end ", JSON.parse(job));
              job = JSON.parse(job);
              io.to(sid).emit("dashboard_data",job);
            });
            dashboard_job.on("error",function(){
              console.log("gearman error");
            });
          });
    }

  });
