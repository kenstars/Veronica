/*
 * Copyright (c) Kannan Piedy
 * Veronica is released under the terms of the Apache License,
 * check the file LICENSE.txt.
 */


var serverIp = '';
var serverPort = '';
var username = '';
var initial_flag = 0;
var counter = 0;
var title_page = '';
var title_header = '';
var bot_id_name = "";
var code = 212;
var inverter = 1;
var location_details = "";
// var typingHtml = '<div class="row typing" style="float:right; clear:both; padding-right:20px;"><img src="image/typing.gif"></div>';
var typingHtml = '<div class="typing" style="float:left; clear:both; padding-right:20px;"><div class="typingBot"><!--<img src="images/bot/icon1.png">--></div><div class="bubbles"><div class="bubble bubble1"></div><div class="bubble bubble2"></div><div class="bubble bubble3"></div><div class="bubble bubble4"></div></div><!--<img src="images/bot/typing.gif">--></div>';
window.speechRecognizer = new webkitSpeechRecognition();


$.ajax({
    type: 'GET',
    url: '../ui_config.json',
    dataType: 'json',
    success: function(config) {
        serverIp = config.serverip;
        serverPort = config.serverport;
        username = config.bot_name;
        title_page = config.title_page;
        title_header = config.title_header;
    },
    async: false
});
var serverUrl = "http://" + serverIp + ":" + serverPort;
var socket = io.connect(serverUrl);
console.log(serverUrl);

function sendChatVoice(text) {
        console.log("send-chat");
        var chatMsg = text;
        if (chatMsg.trim() !== '') {
			var date = new Date();
            var timestamp = date.toString("dd MMM yyyy hh:mm:ss");
            date = new Date(timestamp);
            var time_stamp = date.getTime();
            time_stamp = time_stamp /1000;
            var dataTosSend = {'query': chatMsg, 'timestamp': time_stamp, 'session_id':socket.id, 'username':'admin', 'channel':'web', 'location_details':location_details, 'voice_flag':1};
            console.log("data_to_send",dataTosSend);
            socket.emit('receive_data', dataTosSend);
        }
    }


function startConverting (start = 0) {
        //var speechRecognizer = new webkitSpeechRecognition();
        window.speechRecognizer.continuous = true;
        window.speechRecognizer.interimResults = true;
        window.speechRecognizer.lang = 'en';
        console.log("starting speech");
        if('webkitSpeechRecognition' in window && start === 1){
            var finalTranscripts = '';

            window.speechRecognizer.onresult = function(event){
                var interimTranscripts = '';
				//console.log(event.results);
                for(var i = event.resultIndex; i < event.results.length; i++){
                    var transcript = event.results[i][0].transcript;
                    transcript.replace("\n", "<br>");
                    if(event.results[i].isFinal){
                        finalTranscripts += transcript;
                    }else{
                        interimTranscripts += transcript;
                    }
                }
                //r.innerHTML = finalTranscripts + '<span style="color:#999">' + interimTranscripts + '</span>';
                console.log("====="+finalTranscripts);
                //document.getElementById("input_text").value = finalTranscripts;
                if(finalTranscripts.length !== 0){
                    sendChatVoice(finalTranscripts);
                    console.log(finalTranscripts);
                    finalTranscripts = '';
                }
            };
            window.speechRecognizer.onspeechend = function() {
                window.speechRecognizer.stop();
                $("#mic_off").show();
                $("#mic_on").hide();
                console.log('Speech has stopped being detected');
                
            };
            window.speechRecognizer.onerror = function (event) {
                window.speechRecognizer.stop();
                $("#mic_off").show();
                $("#mic_on").hide();
                console.log("error: ",event.error);
            };
            window.speechRecognizer.start();
            
        }else{
            window.speechRecognizer.stop();
            //r.innerHTML = 'Your browser is not supported. If google chrome, please upgrade!';
            console.log("Either you have stopped recognition or Your browser is not supported. If google chrome, please upgrade!");
        }
        
    }


$(document).ready(function() {

	// veronica

	var $veronica = $("#veronica");
	var $veronica_text = $("#veronica .text");
	var $veronica_line = $("#veronica .line");
	var $veronica_arrow = $("#veronica .arrow");
	var $veronica_message_box = $("#veronica .message-box");
	startConverting(start = 1); 
	var veronica = window.veronica = { }
	var timeout = 0;

	veronica.clear = function(mode) {
		clearTimeout(timeout);
		$veronica.removeClass("mode-text mode-text-black mode-message-box");
		$veronica_text.text("-");
		$veronica_line.css("width", "");
		$veronica_arrow.removeClass("arrow-animation");
		$veronica.addClass("mode-" + (mode ? mode : "text"))
	}

	veronica.textAnimate = function(text) {
		this.clear("text");
		var parts = text.replace(/^\s+|\s+$/g, "").replace(/\s+/g, " ").split(" ");
		if (parts.length == 0 || (parts.length == 1 && parts[0] === "")) {
			$veronica_text.addClass("hidden").text("-");
			$veronica_line.css("width", "");
			$veronica_arrow.addClass("arrow-animation");
			return;
		}
		var i = 0;
		function textAnimate_loop0() {
			$veronica_text.addClass("hidden").text(parts[i].replace(/_+/g, " "));
			$veronica_line.width($veronica_text.width() + 10);
			timeout = setTimeout(textAnimate_loop1, 100);
		}
		function textAnimate_loop1() {
			$veronica_text.removeClass("hidden");
			if (++i < parts.length) {
				timeout = setTimeout(textAnimate_loop0, 400);
			} else {
				timeout = setTimeout(function() {
					$veronica_text.addClass("hidden").text("-");
					$veronica_line.css("width", "");
					$veronica_arrow.addClass("arrow-animation");
				}, 400);
			}
		}
		timeout = setTimeout(textAnimate_loop0);
	}

	veronica.textBlack = function(text) {
		this.clear("text-black");
		$veronica_text.removeClass("hidden").text(text);
	}

	veronica.showMessageBox = function(title, message) {
		this.clear("message-box");
		$veronica_message_box.addClass("hidden");
		$(".message-box-title", $veronica_message_box).text(title);
		$(".message-box-text", $veronica_message_box).text(message ? message : "").append($("<span>").addClass("fast-flash").text("_"));
		setTimeout(function() {
			$veronica_message_box.removeClass("hidden");
		}, 10);
	}

	veronica.hideMessageBox = function(title, message) {
		if ($veronica.hasClass("mode-message-box")) {
			$veronica_message_box.addClass("hidden");
		}
		var self = this;
		setTimeout(function() {
			self.textAnimate("");
		}, 300);
	}

	veronica.enlarge = function(text) {
		this.clear("text");
		$veronica_text.addClass("hidden").text(text);
		$veronica_line.width($veronica_text.width() + 80);
		setTimeout(function() {
			$veronica_text.removeClass("hidden");
		}, 200);
	}

	// other
    
	window.audioSetTimeEvents = function(audio, events) {
		$(audio).on("timeupdate", function() {
			for (var key in events) {
				if (this.currentTime > key) {
					if (typeof events[key] === "function") {
						events[key]();
					} else {
						var obj = (events[key][0] || window);
						obj[events[key][1]].apply(obj, events[key][2]);
					}
					delete events[key];
				}
			}
		});
	}

	window.audioStart = function(audio, time, fadein_time) {
		audio.currentTime = time;
		if (fadein_time) {
			audio.volume = 0;
			$(audio).on("timeupdate", function fn() {
				var dt = this.currentTime - time;
				if (dt < fadein_time) {
					this.volume = dt/fadein_time;
				} else {
					this.volume = 0;
					$(audio).off("timeupdate", fn);
				}
			});
		} else {
			audio.volume = 0;
		}
		audio.play();
	}

	window.tryPlayAudio = function(audio, time, fadein_time) {
		function doPlayAudio() {
			audioStart(audio, time, fadein_time);
			setTimeout(function() {
				if (audio.paused) {
					// mobile browser? we need user interaction
					$(document).click(function fn() {
						$(this).off("click", fn);
						showSubtitle(null);
						audio.play();
					});
					showSubtitle("(tap the screen)", -1);
				}
			}, 100);
		}
		if (audio.readyState == 4) {
			doPlayAudio()
		} else {
			$(audio).on("canplay", function fn() {
				$(this).off("canplay", fn);
				doPlayAudio();
			});
		}
	}

	window.showSubtitle = function(text, time) {
		var $subtitle = $("#subtitle");
		if (!text) {
			$subtitle.css("opacity", "0")
			return;
		}
		$subtitle.text("\"" + text + "\"");
		$subtitle.css("opacity", "");
		if (!time || time >= 0) {
			setTimeout(function() {
				showSubtitle(null);
			}, time || 1500);
		}
	}

});
