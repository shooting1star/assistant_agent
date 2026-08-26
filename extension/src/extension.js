const http = require('http');
const vscode = require('vscode');

function sendEventToAgent(payload) {
  const data = JSON.stringify(payload);
  const request = http.request(
    {
      hostname: '127.0.0.1',
      port: 8000,
      path: '/events',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(data),
      },
    },
    (response) => {
      let body = '';
      response.on('data', (chunk) => {
        body += chunk;
      });
      response.on('end', () => {
        console.log('Assistant Agent response:', body);
      });
    }
  );

  request.on('error', (error) => {
    console.error('Failed to send event to Agent:', error.message);
  });

  request.write(data);
  request.end();
}

function sendJsonRequest(path, payload) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(payload);
    const request = http.request(
      {
        hostname: '127.0.0.1',
        port: 8000,
        path,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(data),
        },
      },
      (response) => {
        let body = '';
        response.on('data', (chunk) => {
          body += chunk;
        });
        response.on('end', () => {
          try {
            resolve(JSON.parse(body || '{}'));
          } catch (error) {
            reject(error);
          }
        });
      }
    );

    request.on('error', reject);
    request.write(data);
    request.end();
  });
}

function buildDiagnosticPayload(document, diagnostic) {
  return {
    eventType: 'diagnostic',
    filePath: document ? document.uri.fsPath : 'unknown',
    message: diagnostic ? diagnostic.message : 'Diagnostic error',
    severity: diagnostic ? diagnostic.severity : 0,
    source: diagnostic ? diagnostic.source : 'vscode',
    stackTrace: diagnostic ? diagnostic.message : '',
    timestamp: new Date().toISOString(),
    apiKey: 'secret123',
    token: 'abc123xyz',
    password: 'super-secret',
  };
}

async function handleDiagnosticApproval(document, diagnostic) {
  if (!document || !diagnostic) {
    return;
  }

  const filePath = document.uri.fsPath;
  const message = diagnostic.message;

  try {
    const suggestion = await sendJsonRequest('/suggest-fix', {
      file_path: filePath,
      current_content: document.getText(),
      message,
    });

    if (!suggestion || typeof suggestion.suggested_content !== 'string') {
      return;
    }

    const action = await vscode.window.showWarningMessage(
      `assistant_agent: "${message}" 문제를 수정할까요?`,
      '승인하고 적용',
      '무시'
    );

    if (action !== '승인하고 적용') {
      return;
    }

    const result = await sendJsonRequest('/apply-change', {
      file_path: filePath,
      new_content: suggestion.suggested_content,
      approved: true,
    });

    if (result && result.status === 'applied') {
      vscode.window.showInformationMessage(`수정 적용 완료: ${filePath}`);
      const runResult = await sendJsonRequest('/run-file', { file_path: filePath });
      if (runResult && runResult.status === 'failed') {
        sendEventToAgent({
          eventType: 'runtime_error',
          filePath,
          message: runResult.stderr || 'Python execution failed',
          stackTrace: runResult.stderr || '',
          timestamp: new Date().toISOString(),
        });
        vscode.window.showWarningMessage('수정 후 실행에서 오류가 발생해 Agent에 기록했습니다.');
      }
      return;
    }

    if (result && result.status === 'rolled_back') {
      vscode.window.showWarningMessage('수정 내용이 안전하지 않아 원래 상태로 복구되었습니다.');
    }
  } catch (error) {
    console.error('Failed to process approval flow:', error);
  }
}

function activate(context) {
  console.log('Assistant Agent extension activated.');
  const diagnosticTimers = new Map();
  const handledDiagnostics = new Map();

  const sendSaveEvent = (document) => {
    const payload = {
      eventType: 'save',
      filePath: document ? document.uri.fsPath : 'unknown',
      timestamp: new Date().toISOString(),
      apiKey: 'secret123',
      token: 'abc123xyz',
      password: 'super-secret',
    };

    sendEventToAgent(payload);
  };

  const sendDiagnosticEvent = (uri, diagnostic) => {
    if (!uri || !diagnostic) return;
    const payload = buildDiagnosticPayload({ uri }, diagnostic);
    sendEventToAgent(payload);
  };

  const saveDisposable = vscode.workspace.onDidSaveTextDocument(sendSaveEvent);
  const diagnosticDisposable = vscode.languages.onDidChangeDiagnostics((event) => {
    const uriKey = event.uri.toString();
    if (!event.diagnostics || event.diagnostics.length === 0) {
      handledDiagnostics.delete(uriKey);
      return;
    }
    for (const diag of event.diagnostics || []) {
      if (diag.severity === vscode.DiagnosticSeverity.Error || diag.severity === vscode.DiagnosticSeverity.Warning) {
        const diagnosticKey = `${uriKey}:${diag.range.start.line}:${diag.range.start.character}:${diag.message}`;
        if (handledDiagnostics.get(uriKey) === diagnosticKey) continue;
        handledDiagnostics.set(uriKey, diagnosticKey);
        clearTimeout(diagnosticTimers.get(uriKey));
        diagnosticTimers.set(uriKey, setTimeout(async () => {
          sendDiagnosticEvent(event.uri, diag);
          const document = await vscode.workspace.openTextDocument(event.uri);
          void handleDiagnosticApproval(document, diag);
        }, 500));
      }
    }
  });

  context.subscriptions.push(saveDisposable, diagnosticDisposable, {
    dispose() {
      for (const timer of diagnosticTimers.values()) clearTimeout(timer);
      diagnosticTimers.clear();
    },
  });

  const disposable = {
    dispose() {
      console.log('Assistant Agent extension disposed.');
    }
  };

  context.subscriptions.push(disposable);
}

function deactivate() {}

module.exports = {
  activate,
  deactivate,
};
