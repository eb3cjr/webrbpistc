const express = require('express')
const path = require ('path')
const fs = require ('fs')
const sqlite3 = require('sqlite3').verbose()
const { engine } = require('express-handlebars');
const app = express();

app.engine('hbs', engine({ extname: '.hbs', defaultLayout: "index", layoutsdir: ""}));
app.set('view engine', 'hbs');

//defineix port
const port = 8090                                     

app.get('/', (req, res) => {

  // open database in memory. work in progress!!

  let db = new sqlite3.Database('/home/pi/Current-Power_Monitor_HAT/RaspberryPi/STC_Voltage.db', (err) => {
  if (err) {
      return console.error(err.message);
    }
    console.log('Connected to the in-memory SQlite database.');
     
    res.render(path.join(__dirname,'./views/view'), {
        author: 'Súper RG & RR',
        date: '06_01_2022',
        }
    );
  });

})

app.listen(port, () => {
  console.log(`Example app listening at http://localhost:${port}`)
})




