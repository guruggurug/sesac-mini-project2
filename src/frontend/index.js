document.addEventListener('DOMContentLoaded', () => {
    const portfolioForm = document.getElementById('portfolio-form');
    const resultsArea = document.getElementById('results-area');
    const dataStatusBadge = document.getElementById('data-status-badge');

    // API URL 설정 (개발 모드에 맞춰 포트 설정 가능)
    const API_BASE_URL = 'http://localhost:8000';

    portfolioForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const samsungShares = parseInt(document.getElementById('samsung-shares').value) || 0;
        const samsungPrice = parseInt(document.getElementById('samsung-price').value) || 0;
        const hynixShares = parseInt(document.getElementById('hynix-shares').value) || 0;
        const hynixPrice = parseInt(document.getElementById('hynix-price').value) || 0;

        // 로딩 상태 표시
        showLoadingState();

        try {
            // API 호출 시도
            const response = await fetch(`${API_BASE_URL}/portfolio/calculate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    samsung: { shares: samsungShares, price: samsungPrice },
                    hynix: { shares: hynixShares, price: hynixPrice }
                })
            });

            if (!response.ok) {
                throw new Error('API server returned error');
            }

            const data = await response.json();
            renderResults(data);
        } catch (error) {
            console.warn('API fetch failed, falling back to local mock calculations:', error);
            // 백엔드가 아직 준비되지 않은 경우를 위한 클라이언트 사이드 mock 계산 및 처리
            simulateCalculation(samsungShares, samsungPrice, hynixShares, hynixPrice);
        }
    });

    function showLoadingState() {
        resultsArea.innerHTML = `
            <div class="loading-state card">
                <div class="spinner"></div>
                <p>포트폴리오 분석 중...</p>
            </div>
        `;
    }

    function simulateCalculation(samShares, samPrice, hynShares, hynPrice) {
        const samValue = samShares * samPrice;
        const hynValue = hynShares * hynPrice;
        const totalValue = samValue + hynValue;

        if (totalValue === 0) {
            resultsArea.innerHTML = `
                <div class="empty-state card">
                    <p>유효한 자산 가치가 0원입니다. 수량과 가격을 확인해 주세요.</p>
                </div>
            `;
            return;
        }

        const samWeight = (samValue / totalValue) * 100;
        const hynWeight = (hynValue / totalValue) * 100;

        // 모의 추천 최적화 비중 계산 (50:50으로 유도하는 임의 룰)
        let recSamWeight = 50;
        let recHynWeight = 50;

        if (samWeight > 70) {
            recSamWeight = 60;
            recHynWeight = 40;
        } else if (hynWeight > 70) {
            recSamWeight = 40;
            recHynWeight = 60;
        }

        setTimeout(() => {
            renderResults({
                state: 'sample',
                current: {
                    samsung: samWeight.toFixed(1),
                    hynix: hynWeight.toFixed(1)
                },
                recommended: {
                    samsung: recSamWeight,
                    hynix: recHynWeight
                },
                risk: {
                    samsung_cvar: '4.2%',
                    hynix_cvar: '5.1%',
                    samsung_esg: 'Medium (Grade B)',
                    hynix_esg: 'Low (Grade A)'
                },
                explanation: '현재 포트폴리오가 한 종목에 다소 쏠려 있어, ESG 관리위험 및 가격 하방위험을 완화하기 위해 비중 조정(최대 80% 제한)을 추천합니다.'
            });
        }, 1000);
    }

    function renderResults(data) {
        // 데이터 상태에 따른 배지 업데이트
        if (data.state === 'reviewed') {
            dataStatusBadge.textContent = 'Reviewed Data';
            dataStatusBadge.className = 'data-badge badge-reviewed';
        } else {
            dataStatusBadge.textContent = 'Sample Data';
            dataStatusBadge.className = 'data-badge badge-sample';
        }

        resultsArea.innerHTML = `
            <!-- 비중 비교 -->
            <div class="card result-card">
                <h3 class="section-title">📊 포트폴리오 비중 비교</h3>
                <div class="comparison-row">
                    <div class="comp-box">
                        <span class="comp-label">현재 비중</span>
                        <div class="comp-bar-container">
                            <div class="comp-bar sam-bar" style="width: ${data.current.samsung}%">삼성 ${data.current.samsung}%</div>
                            <div class="comp-bar hyn-bar" style="width: ${data.current.hynix}%">하이닉스 ${data.current.hynix}%</div>
                        </div>
                    </div>
                    <div class="comp-box" style="margin-top: 15px;">
                        <span class="comp-label">추천 비중</span>
                        <div class="comp-bar-container">
                            <div class="comp-bar sam-bar" style="width: ${data.recommended.samsung}%">삼성 ${data.recommended.samsung}%</div>
                            <div class="comp-bar hyn-bar" style="width: ${data.recommended.hynix}%">하이닉스 ${data.recommended.hynix}%</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 위험 진단 지표 -->
            <div class="card result-card">
                <h3 class="section-title">⚠️ 개별 위험 지표</h3>
                <table class="risk-table">
                    <thead>
                        <tr>
                            <th>종목</th>
                            <th>가격 CVaR (95%)</th>
                            <th>ESG 관리위험</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>삼성전자</td>
                            <td>${data.risk.samsung_cvar}</td>
                            <td>${data.risk.samsung_esg}</td>
                        </tr>
                        <tr>
                            <td>SK하이닉스</td>
                            <td>${data.risk.hynix_cvar}</td>
                            <td>${data.risk.hynix_esg}</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- 분석 의견 -->
            <div class="card result-card">
                <h3 class="section-title">📝 포트폴리오 처방전</h3>
                <p class="explanation-text">${data.explanation}</p>
            </div>
        `;
    }
});
