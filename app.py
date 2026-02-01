import streamlit as st
import akshare as ak
import pandas as pd
import time

# 页面配置
st.set_page_config(page_title="我的基金估值神器", page_icon="📈")

st.title("🚀 简易版基金实时估值")
st.markdown("原理：基于最新季度前十大重仓股的实时涨跌幅进行估算。")

# 输入框
fund_code = st.text_input("请输入基金代码 (例如：161725 招商白酒)", "161725")

if st.button("开始计算"):
    with st.spinner('正在分析持仓数据，请稍等...'):
        try:
            # 1. 获取基金基本信息（为了拿名字）
            # 注意：实际接口可能会变，这里做容错处理
            st.info(f"正在查询基金 {fund_code} 的重仓股...")
            
            # 获取基金持仓 (默认获取最新日期)
            # AkShare 接口：fund_portfolio_em
            portfolio_df = ak.fund_portfolio_em(symbol=fund_code)
            
            # 简单清洗数据：只要 股票代码、股票名称、占净值比例
            # 注意：接口返回的列名是中文
            portfolio_df = portfolio_df[['股票代码', '股票名称', '占净值比例']]
            
            # 转换为数值类型
            portfolio_df['占净值比例'] = pd.to_numeric(portfolio_df['占净值比例'], errors='coerce')
            
            # 显示前十大重仓
            st.subheader("📊 前十大重仓股快照")
            st.dataframe(portfolio_df.head(10))
            
            # 2. 获取实时行情并计算
            st.info("正在拉取实时股价...")
            
            total_estimate = 0.0
            total_weight = 0.0
            
            # 创建一个进度条
            progress_bar = st.progress(0)
            top_10 = portfolio_df.head(10)
            
            details = []
            
            for index, row in top_10.iterrows():
                stock_code = row['股票代码']
                stock_name = row['股票名称']
                weight = row['占净值比例']
                
                # 更新进度条
                progress_bar.progress((index + 1) / 10)
                
                try:
                    # 获取个股实时行情
                    stock_spot = ak.stock_zh_a_spot_em()
                    # 筛选该股票
                    stock_info = stock_spot[stock_spot['代码'] == stock_code]
                    
                    if not stock_info.empty:
                        change_percent = stock_info.iloc[0]['涨跌幅']
                        contribution = change_percent * (weight / 100)
                        
                        total_estimate += contribution
                        total_weight += weight
                        
                        details.append({
                            "股票": stock_name,
                            "权重": f"{weight}%",
                            "实时涨跌": f"{change_percent}%",
                            "贡献度": f"{contribution:.4f}"
                        })
                    else:
                        # 可能是港股或其他，暂时跳过
                        pass
                        
                except Exception as e:
                    pass
            
            # 3. 结果展示
            st.success("计算完成！")
            
            # 粗略修正：假设剩余仓位（非前十大）走势与前十大一致
            if total_weight > 0:
                final_estimate = total_estimate * (100 / total_weight)
            else:
                final_estimate = 0
                
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="前十大重仓估值", value=f"{total_estimate:.2f}%")
            with col2:
                st.metric(label="全仓推算估值", value=f"{final_estimate:.2f}%", delta=f"{final_estimate:.2f}%")
            
            with st.expander("查看详细计算过程"):
                st.table(pd.DataFrame(details))
                
        except Exception as e:
            st.error(f"发生错误：{e}")
            st.warning("提示：可能是基金代码错误，或者AkShare接口暂时不稳定。")
