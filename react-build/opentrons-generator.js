/**
 * Opentrons Code Generator UI Component
 * 
 * Simple UI for displaying Opentrons code generation status and results
 */

class OpentronsGenerator {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.status = {
            stage: 'idle', // idle, generating, validating, retrying, success, failed
            progress: 0,
            message: '',
            errors: [],
            code: '',
            attempts: 0,
            maxAttempts: 3
        };
        
        this.init();
    }
    
    init() {
        this.render();
    }
    
    render() {
        this.container.innerHTML = `
            <div class="opentrons-generator">
                <div class="opentrons-header">
                    <h3>🤖 Opentrons Protocol Generator</h3>
                    <div class="status-indicator ${this.status.stage}">
                        ${this.getStatusIcon()} ${this.getStatusText()}
                    </div>
                </div>
                
                <div class="progress-container">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${this.status.progress}%"></div>
                    </div>
                    <div class="progress-text">${this.status.message}</div>
                </div>
                
                ${this.status.attempts > 0 ? `
                    <div class="attempts-info">
                        Attempt ${this.status.attempts} of ${this.status.maxAttempts}
                    </div>
                ` : ''}
                
                ${this.status.errors.length > 0 ? `
                    <div class="errors-container">
                        <h4>Errors:</h4>
                        <ul class="error-list">
                            ${this.status.errors.map(error => `<li>${error}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                
                ${this.status.code ? `
                    <div class="code-container">
                        <h4>Generated Code:</h4>
                        <pre><code class="python">${this.status.code}</code></pre>
                        <div class="code-actions">
                            <button onclick="this.copyCode()" class="btn-copy">Copy Code</button>
                            <button onclick="this.downloadCode()" class="btn-download">Download</button>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
        
        this.addStyles();
    }
    
    getStatusIcon() {
        const icons = {
            'idle': '⏸️',
            'generating': '🔄',
            'validating': '🔍',
            'retrying': '🔄',
            'success': '✅',
            'failed': '❌'
        };
        return icons[this.status.stage] || '❓';
    }
    
    getStatusText() {
        const texts = {
            'idle': 'Ready',
            'generating': 'Generating Code...',
            'validating': 'Validating with Simulation...',
            'retrying': 'Retrying Generation...',
            'success': 'Success!',
            'failed': 'Failed'
        };
        return texts[this.status.stage] || 'Unknown';
    }
    
    updateStatus(newStatus) {
        this.status = { ...this.status, ...newStatus };
        this.render();
    }
    
    setStage(stage, message = '') {
        this.updateStatus({ 
            stage, 
            message,
            progress: this.getProgressForStage(stage)
        });
    }
    
    getProgressForStage(stage) {
        const progressMap = {
            'idle': 0,
            'generating': 30,
            'validating': 70,
            'retrying': 50,
            'success': 100,
            'failed': 100
        };
        return progressMap[stage] || 0;
    }
    
    addErrors(errors) {
        this.updateStatus({ 
            errors: [...this.status.errors, ...errors] 
        });
    }
    
    setCode(code) {
        this.updateStatus({ code });
    }
    
    incrementAttempts() {
        this.updateStatus({ 
            attempts: this.status.attempts + 1 
        });
    }
    
    reset() {
        this.updateStatus({
            stage: 'idle',
            progress: 0,
            message: '',
            errors: [],
            code: '',
            attempts: 0
        });
    }
    
    copyCode() {
        if (this.status.code) {
            navigator.clipboard.writeText(this.status.code).then(() => {
                alert('Code copied to clipboard!');
            });
        }
    }
    
    downloadCode() {
        if (this.status.code) {
            const blob = new Blob([this.status.code], { type: 'text/python' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'opentrons_protocol.py';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
    }
    
    addStyles() {
        if (document.getElementById('opentrons-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'opentrons-styles';
        style.textContent = `
            .opentrons-generator {
                border: 1px solid #e1e5e9;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
                background: #f8f9fa;
            }
            
            .opentrons-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }
            
            .opentrons-header h3 {
                margin: 0;
                color: #2c3e50;
            }
            
            .status-indicator {
                padding: 8px 16px;
                border-radius: 20px;
                font-weight: bold;
                font-size: 14px;
            }
            
            .status-indicator.idle { background: #e9ecef; color: #6c757d; }
            .status-indicator.generating { background: #fff3cd; color: #856404; }
            .status-indicator.validating { background: #d1ecf1; color: #0c5460; }
            .status-indicator.retrying { background: #f8d7da; color: #721c24; }
            .status-indicator.success { background: #d4edda; color: #155724; }
            .status-indicator.failed { background: #f8d7da; color: #721c24; }
            
            .progress-container {
                margin-bottom: 20px;
            }
            
            .progress-bar {
                width: 100%;
                height: 8px;
                background: #e9ecef;
                border-radius: 4px;
                overflow: hidden;
                margin-bottom: 8px;
            }
            
            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #007bff, #0056b3);
                transition: width 0.3s ease;
            }
            
            .progress-text {
                font-size: 14px;
                color: #6c757d;
                text-align: center;
            }
            
            .attempts-info {
                text-align: center;
                font-size: 12px;
                color: #6c757d;
                margin-bottom: 15px;
            }
            
            .errors-container {
                background: #f8d7da;
                border: 1px solid #f5c6cb;
                border-radius: 4px;
                padding: 15px;
                margin-bottom: 20px;
            }
            
            .errors-container h4 {
                margin: 0 0 10px 0;
                color: #721c24;
            }
            
            .error-list {
                margin: 0;
                padding-left: 20px;
                color: #721c24;
            }
            
            .code-container {
                background: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 15px;
            }
            
            .code-container h4 {
                margin: 0 0 15px 0;
                color: #2c3e50;
            }
            
            .code-container pre {
                background: #2d3748;
                color: #e2e8f0;
                padding: 15px;
                border-radius: 4px;
                overflow-x: auto;
                margin-bottom: 15px;
            }
            
            .code-actions {
                display: flex;
                gap: 10px;
            }
            
            .btn-copy, .btn-download {
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
            }
            
            .btn-copy {
                background: #007bff;
                color: white;
            }
            
            .btn-download {
                background: #28a745;
                color: white;
            }
            
            .btn-copy:hover, .btn-download:hover {
                opacity: 0.8;
            }
        `;
        
        document.head.appendChild(style);
    }
}

// Global functions for easy access
window.OpentronsGenerator = OpentronsGenerator;

// Example usage:
// const generator = new OpentronsGenerator('opentrons-container');
// generator.setStage('generating', 'Creating Opentrons protocol...');
// generator.setStage('validating', 'Running simulation...');
// generator.setCode('print("Hello Opentrons!")');
// generator.setStage('success');
