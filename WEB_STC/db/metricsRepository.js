const sqlite3 = require('sqlite3');

module.exports = class MetricsRepository {
    static dbPath = '/home/pi/Current-Power_Monitor_HAT/RaspberryPi/STC_Voltage.db';
    // static dbPath = '../STC_Voltage.db';

    /**
     * Returns the latest metrics from the RaspberryPi.
     */
    static async getRaspberryLatestsMetrics() {
        // we supose nothing bad happens so we don't handle possible errors
        const dbCon = await MetricsRepository._connectToDB();
        const statement = `SELECT (cpu_temp AS cpuTemp, psu_vol_sol_1 AS psuVolSol1,
            psu_vol_bat_1 AS psuVolBat1, psu_vol_bat_2 AS psuVolBat2,
            psu_vol_rb_pi AS psuVolRbPi, timestamp)
            FROM stc_bat_dades
            ORDER BY timestamp DESC;`;

        const rows = await MetricsRepository._promisifyAll(dbCon, statement);
        dbCon.close();
        return rows[0];
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
