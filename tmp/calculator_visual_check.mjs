import fs from 'node:fs';

const endpoint = 'http://127.0.0.1:9224/json';

async function delay(ms) {
  await new Promise((resolve) => setTimeout(resolve, ms));
}

let targets;
for (let attempt = 0; attempt < 30; attempt += 1) {
  try {
    targets = await (await fetch(endpoint)).json();
    break;
  } catch {
    await delay(100);
  }
}
if (!targets?.length) {
  throw new Error('Chrome DevTools target is unavailable');
}
console.log('target-ready');

const socket = new WebSocket(targets[0].webSocketDebuggerUrl);
await new Promise((resolve, reject) => {
  socket.addEventListener('open', resolve, {once: true});
  socket.addEventListener('error', reject, {once: true});
});
console.log('socket-ready');

let id = 0;
const pending = new Map();
socket.addEventListener('message', (event) => {
  const message = JSON.parse(event.data);
  if (!message.id || !pending.has(message.id)) {
    return;
  }
  const {resolve, reject} = pending.get(message.id);
  pending.delete(message.id);
  if (message.error) {
    reject(new Error(message.error.message));
  } else {
    resolve(message.result);
  }
});

function command(method, params = {}) {
  id += 1;
  const requestId = id;
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      pending.delete(requestId);
      reject(new Error(`Chrome DevTools command timed out: ${method}`));
    }, 5000);
    pending.set(requestId, {
      resolve(value) {
        clearTimeout(timeout);
        resolve(value);
      },
      reject(error) {
        clearTimeout(timeout);
        reject(error);
      },
    });
    socket.send(JSON.stringify({id: requestId, method, params}));
  });
}

async function evaluate(expression) {
  return command('Runtime.evaluate', {
    expression,
    awaitPromise: true,
    returnByValue: true,
  });
}

async function render(width, height, output) {
  await command('Emulation.setDeviceMetricsOverride', {
    width,
    height,
    deviceScaleFactor: 1,
    mobile: width < 600,
  });
  await command('Page.navigate', {
    url: 'http://127.0.0.1:4174/Калькулятор/',
  });
  await delay(800);

  for (const value of ['1000000', '15', '300000', '50000']) {
    await evaluate(`document.querySelector('input').focus()`);
    await command('Input.insertText', {text: value});
    await delay(120);
    await evaluate(`document.querySelector('button.bg-amber-500').click()`);
    await delay(350);
  }

  const labels = await evaluate(`({
    title: document.querySelector('h1')?.textContent?.trim(),
    result: document.querySelector('#calculation-result-title')?.textContent?.trim(),
    benefit: [...document.querySelectorAll('p')].find(
      (node) => node.textContent.includes('При работе на ИУ')
    )?.textContent?.trim()
  })`);
  const metrics = await command('Page.getLayoutMetrics');
  const screenshot = await command('Page.captureScreenshot', {
    format: 'png',
    captureBeyondViewport: true,
    clip: {
      x: 0,
      y: 0,
      width: metrics.cssContentSize.width,
      height: metrics.cssContentSize.height,
      scale: 1,
    },
  });
  fs.writeFileSync(output, Buffer.from(screenshot.data, 'base64'));
  return labels.result.value;
}

await command('Page.enable');
await command('Runtime.enable');
console.log('protocol-ready');

const mobile = await render(
  390,
  844,
  'C:/Users/Администратор/Новая папка/hermes-brain/tmp/calculator-mobile-v2.png'
);
const desktop = await render(
  1440,
  1000,
  'C:/Users/Администратор/Новая папка/hermes-brain/tmp/calculator-desktop-v2.png'
);
console.log(JSON.stringify({mobile, desktop}, null, 2));
socket.close();
