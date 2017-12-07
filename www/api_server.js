var express = require('express');
var app = express();
var fs = require("fs");
var SentenceTypeClassifier = require("sentence-type-classifier");

app.get('/question_classifier', function (req, res) {
  console.log("@@Incoming from ChatWorker@@");
  var classifier = new SentenceTypeClassifier();
  var data_json=req.query;
  console.log(data_json)
  incoming_text = data_json.text
  console.log(incoming_text)
  var classification_result = classifier.classify(incoming_text);
  res.status(200).json({ result: classification_result });
})

var server = app.listen(5000, function () {

  var host = server.address().address
  var port = server.address().port
  console.log("Question Clasifier listening at http://%s:%s", host, port)

})