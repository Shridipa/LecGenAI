const localtunnel = require('localtunnel');
const fs = require('fs');

(async () => {
  console.log('🔄 Starting Backup Tunnel (Localtunnel)...');
  try {
    const tunnel = await localtunnel({ port: 8000 });
    console.log('\n🚀 BACKUP TUNNEL ONLINE!');
    console.log('🔗 URL:', tunnel.url);
    console.log('\n1. PLEASE COPY THIS URL ABOVE');
    console.log('2. PASTE IT INTO THE CHAT SO I CAN UPDATE VERCEL.');
    
    fs.writeFileSync('URL_LOCALTUNNEL.txt', tunnel.url);
    
    tunnel.on('close', () => {
       console.log('Tunnel closed');
    });
    
    // Keep alive
    setInterval(() => {}, 10000);
  } catch (err) {
    console.error('❌ Localtunnel Error:', err.message);
  }
})();
