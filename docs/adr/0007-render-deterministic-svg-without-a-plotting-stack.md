# 使用纯 Python 生成确定性 SVG

状态：已被 ADR 0011 取代。

技术面图表继续由纯 Python renderer 直接序列化 SVG，不依赖浏览器、HTML、matplotlib 或
mplfinance。相同技术面证据集必须生成字节稳定、可访问且可离线验收的图表；我们接受自行维护
K 线、成交量、均线和关键位绘制逻辑，以换取轻量依赖、跨阅读器展示和精确审计能力。
