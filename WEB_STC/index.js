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

app.get('/', async (req, res) => {
  const { cpuTemp, psuVolSol1, psuVolBat1, psuVolBat2, psuVolRbPi, timestamp } =
    await MetricsRepository.getRaspberryLatestsMetrics();
  const { cpuTempMax, psuVol1Max, psuBat1Max, psuBat2Max, psuRbPiMax } =
    await MetricsRepository.getRaspberryMaxMetrics();
  res.render(path.join(__dirname,'./views/view'), {
    author: 'Súper RG & RR',
    date: '06_01_2022',
    cpuTemp,
    psuVolSol1,
    psuVolBat1,
    psuVolBat2,
    psuVolRbPi,
    timestamp,
    cpuTempMax: {
      ...cpuTempMax,
      timestamp: new Date(cpuTempMax.timestamp)
    },
    psuVol1Max: {
      ...psuVol1Max,
      timestamp: new Date(psuVol1Max.timestamp)
    },
    psuBat1Max: {
      ...psuBat1Max,
      timestamp: new Date(psuBat1Max.timestamp)
    },
    psuBat2Max: {
      ...psuBat2Max,
      timestamp: new Date(psuBat2Max.timestamp)
    },
    psuRbPiMax: {
      ...psuRbPiMax,
      timestamp: new Date(psuRbPiMax.timestamp)
    }
  });
})

app.listen(port, () => {
  console.log(`Example app listening at http://localhost:${port}`)
})




