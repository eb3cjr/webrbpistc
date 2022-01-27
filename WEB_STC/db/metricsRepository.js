const sqlite3 = require('sqlite3');

module.exports = class MetricsRepository {
    static dbPath = '/home/pi/Current-Power_Monitor_HAT/RaspberryPi/STC_Voltage.db';
    // static dbPath = '../STC_Voltage.db';

    /**
     * Returns an object that contains different properties
     * from the RaspberryPi.
     */
    static async getRaspberryMetrics() {
        // we supose nothing bad happens so we don't handle possible errors
        const dbCon = await MetricsRepository._connectToDB();
        const statement = `SELECT cpu_temp FROM stc_bat_dades;`;
        const rows = await MetricsRepository._promisifyAll(dbCon, statement);
        console.log(rows);
        dbCon.close();
    }

    /**
     * Returns a promise that is resolved when a connection to the DB
     * is stablished.
     */
    static _connectToDB() {
        return new Promise((resolve, reject) => {
            const con = new sqlite3.Database('../STC_Voltage.db', (err) => {
                if (err) {
                    reject(error);
                }
                resolve(con);
            });
        });
    }

    /**
     * Returns a promise when the all callback gets resolved.
     * @param dbCon The connection to the db
     * @param statement The SQL statement that needs to be executed
     * @returns a promise that is fulfilled when the data is retrieved from the BD
     */
    static _promisifyAll(dbCon, statement) {
        return new Promise((resolve, reject) => {
            dbCon.all(statement, [], (err, rows) => {
                if (err) {
                  reject(error);
                }
                resolve(rows);
            });
        });
    }
}
