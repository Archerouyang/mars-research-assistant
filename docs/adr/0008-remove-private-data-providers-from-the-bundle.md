# 从组合包删除私密数据源

Mars Research Assistant 不读取、探测、保存或使用 FMP、API key 或其他私密 Provider。
技术面分析的 OHLCV 只使用 yfinance 公开 best-effort 数据；市场快照、市场催化剂简报和标的
研究仍可访问各自所需的政府、监管机构、交易所、发行人等公开来源。我们放弃付费数据源和
自动回退能力，以换取零凭据安装、清晰的数据契约和更小的 RED Skill 权限面。
