var http = require("http"),
send = require('send'),
url = require('url'),
_ = require('underscore');
var fs = require("fs");
var config = JSON.parse(fs.readFileSync('../config.json', 'utf8'));
var serverIp = config.serverip;
var serverPort = config.serverport;



//App core
var app = http.createServer(function(req, res) {

    //Http Error Handler
    function error(err) {
        res.statusCode = err.status || 500;
        res.setHeader('Content-Type', 'text/html');
        res.end("<span style='font: 15px Tahoma; color: red'>Error: </span><span'>Page not Found! <br>Click <a href='http://"+serverIp+":"+serverPort+"''>here</a> to go to Home Page...</span></span>");
    }

    //Http Redirect Handler
    function redirect() {
        res.statusCode = 301;
        res.setHeader('Location', req.url + '/');
        res.end('Redirecting to ' + req.url + '/');
    }

    //Http Root
    function setRoot(){
        res.setHeader("Access-Control-Allow-Origin", "*");
        return '../www/';
    }

    //Http Set Index
    function setIndex(){
        res.setHeader("Access-Control-Allow-Origin", "*");
        return '../www/index.html';
    }

	//Http Return Pipe
	send(req, url.parse(req.url).pathname, {root: setRoot(), index: setIndex(),extensions:['html', 'htm']})
	    .on('error', error)
	    .on('directory', redirect)
	    .pipe(res);

}).listen(serverPort);
