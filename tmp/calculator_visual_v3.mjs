import fs from 'node:fs';

const endpoint = 'http://127.0.0.1:9225/json';
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

let targets;
for (let attempt = 0; attempt < 40; attempt += 1) {
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
  const request = pending.get(message.id);
  if (!request) {
    return;
  }
  pending.delete(message.id);
  message.error
    ? request.reject(new Error(message.error.message))
    : request.resolve(message.result);
});

function command(method, params = {}) {
  id += 1;
  const requestId = id;
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      pending.delete(requestId);
      reject(new Error(`Chrome DevTools command timed out: ${method}`));
    }, 20000);
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

async function screenshot(width, height, output, scrollExpression) {
  await command('Emulation.setDeviceMetricsOverride', {
    width,
    height,
    deviceScaleFactor: 1,
    mobile: width < 600,
  });
  await evaluate(scrollExpression);
  await delay(250);
  const image = await command('Page.captureScreenshot', {
    format: 'png',
    fromSurface: true,
  });
  fs.writeFileSync(output, Buffer.from(image.data, 'base64'));
}

await command('Page.enable');
await command('Runtime.enable');
console.log('protocol-ready');
await command('Emulation.setDeviceMetricsOverride', {
  width: 390,
  height: 844,
  deviceScaleFactor: 1,
  mobile: true,
});
await command('Page.navigate', {
  url: 'http://127.0.0.1:4175/Калькулятор/',
});
await delay(800);

for (const [index, value] of ['1000000', '15', '300000', '50000'].entries()) {
  await evaluate(`document.querySelectorAll('input')[${index}].focus()`);
  await command('Input.insertText', {text: value});
}
await evaluate(`document.querySelector('button[type="submit"]').click()`);
await delay(600);

const labels = await evaluate(`({
  title: document.querySelector('h1')?.textContent?.trim(),
  result: document.querySelector('#calculation-result-title')?.textContent?.trim(),
  inputCount: document.querySelectorAll('input').length,
  darkBackground: document.querySelector('main')?.className.includes('zinc-950')
})`);

await screenshot(
  390,
  844,
  'C:/Users/Администратор/Новая папка/hermes-brain/tmp/calculator-light-mobile-form.png',
  `window.scrollTo({top: 0, behavior: 'instant'})`,
);
await screenshot(
  390,
  844,
  'C:/Users/Администратор/Новая папка/hermes-brain/tmp/calculator-light-mobile-result.png',
  `document.querySelector('#calculation-result-title').scrollIntoView({block: 'start', behavior: 'instant'})`,
);
await screenshot(
  1440,
  1000,
  'C:/Users/Администратор/Новая папка/hermes-brain/tmp/calculator-light-desktop-form.png',
  `window.scrollTo({top: 0, behavior: 'instant'})`,
);
await screenshot(
  1440,
  1000,
  'C:/Users/Администратор/Новая папка/hermes-brain/tmp/calculator-light-desktop-result.png',
  `document.querySelector('#calculation-result-title').scrollIntoView({block: 'start', behavior: 'instant'})`,
);

console.log(JSON.stringify(labels.result.value, null, 2));
socket.close();
