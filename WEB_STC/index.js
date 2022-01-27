const express = require('express')
const path = require ('path')
const fs = require ('fs')
const sqlite3 = require('sqlite3').verbose()
const { engine } = require('express-handlebars');
const app = express();

const MetricsRepository = require('./db/metricsRepository');

app.engine('hbs', engine({ extname: '.hbs', defaultLayout: "index", layoutsdir: ""}));
app.set('view engine', 'hbs');

//defineix port
const port = 8090

app.get('/', (req, res) => {
  MetricsRepository.getRaspberryMetrics();
  res.render(path.join(__dirname,'./views/view'), {
    author: 'Súper RG & RR',
    date: '06_01_2022',
  });

})

app.listen(port, () => {
  console.log(`Example app listening at http://localhost:${port}`)
})




