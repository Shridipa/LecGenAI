const localtunnel = require('localtunnel');
const fs = require('fs');

(async () => {
  console.log('Starting tunnel...');
  try {
    const tunnel = await localtunnel({ port: 8000 });
    console.log('SUCCESS! URL:', tunnel.url);
    fs.writeFileSync('C:/Users/KIIT/LecGenAICTE/URL_FOUND.txt', tunnel.url);
    console.log('Saved to URL_FOUND.txt');
    
    tunnel.on('close', () => {
       console.log('Tunnel closed');
    });
    
    // Keep process alive
    setInterval(() => {}, 1000);
  } catch (err) {
    console.error('CRITICAL ERROR:', err);
    fs.writeFileSync('C:/Users/KIIT/LecGenAICTE/URL_ERROR.txt', err.stack);
  }
})();
