"""
简约版AutoGen系统使用示例
展示AutoGen多智能体协作的核心优势
"""

import os
from simple_autogen_system import SimpleAutoGenSystem


def main():
    """主函数，演示如何使用简约版AutoGen系统"""
    # 获取API密钥
    # 方式1：直接设置
    # api_key = "your-openai-api-key"
    
    # 方式2：从环境变量获取
    api_key = os.environ.get('OPENAI_API_KEY')
    
    if not api_key:
        print("请设置OpenAI API密钥！")
        print("方法1：在代码中直接设置 api_key = 'your-api-key'")
        print("方法2：设置环境变量 OPENAI_API_KEY=your-api-key")
        return
    
    try:
        # 创建系统实例
        print("创建AutoGen系统...")
        system = SimpleAutoGenSystem(api_key)
        
        # 分析股票
        stock_symbol = "AAPL"  # 苹果公司
        print(f"开始分析股票 {stock_symbol}...")
        print(f"AutoGen系统正在启动多智能体协作流程...\n")
        result = system.analyze_stock(stock_symbol)
        
        # 检查结果
        if 'error' in result:
            print(f"分析失败: {result['error']}")
        else:
            # 打印结果摘要
            print(f"\n===== {result['company_name']}({result['symbol']}) AutoGen多智能体协作分析结果 =====")
            print(f"分析日期: {result['analysis_date']}")
            print(f"AutoGen协作摘要: {result['autogen_collaboration_summary']}")
            
            # 打印财务指标摘要
            print("\n关键财务指标 (百分比):")
            financial = result['financial_metrics']
            print(f"- 净资产收益率(ROE): {financial['roe']:.2f}%")
            print(f"- 总资产收益率(ROA): {financial['roa']:.2f}%")
            print(f"- 资产负债率: {financial['debt_ratio']:.2f}%")
            print(f"- 毛利率: {financial['gross_margin']:.2f}%")
            print(f"- 净利率: {financial['net_margin']:.2f}%")
            print(f"- 流动比率: {financial['current_ratio']:.2f}")
            
            # 打印风险指标摘要
            print("\n风险指标:")
            risk = result['risk_metrics']
            print(f"- 波动率: {risk['volatility']:.4f}")
            print(f"- 95% VaR: {risk['var_95']:.4f}")
            print(f"- 最大回撤: {risk['max_drawdown']:.4f}")
            
            # 打印各智能体分析结果
            print("\n\n=========== AutoGen智能体分析过程展示 ===========")
            print(f"\n--- 数据分析师分析结果 ---")
            print(result['data_analysis'])
            
            print(f"\n--- 财务分析师分析结果 ---")
            print(result['financial_analysis'])
            
            print(f"\n--- 风险分析师分析结果 ---")
            print(result['risk_analysis'])
            
            print(f"\n--- 投资顾问最终建议 ---")
            print(result['investment_advice'])
            
            # 保存报告到文件
            report_file = f"{stock_symbol}_autogen_analysis_report.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(f"# {result['company_name']}({result['symbol']}) AutoGen多智能体分析报告\n")
                f.write(f"分析日期: {result['analysis_date']}\n")
                f.write(f"AutoGen协作摘要: {result['autogen_collaboration_summary']}\n\n")
                
                f.write("## 关键财务指标 (百分比)\n")
                for key, value in financial.items():
                    if key in ['roe', 'roa', 'debt_ratio', 'gross_margin', 'net_margin']:
                        f.write(f"- {key}: {value:.2f}%\n")
                    else:
                        f.write(f"- {key}: {value:.2f}\n")
                
                f.write("\n## 风险指标\n")
                for key, value in risk.items():
                    f.write(f"- {key}: {value:.4f}\n")
                
                f.write("\n\n## ==== AutoGen智能体协作分析过程 ====\n")
                f.write("\n### 1. 数据分析师分析结果\n")
                f.write(result['data_analysis'] + "\n\n")
                
                f.write("### 2. 财务分析师分析结果\n")
                f.write(result['financial_analysis'] + "\n\n")
                
                f.write("### 3. 风险分析师分析结果\n")
                f.write(result['risk_analysis'] + "\n\n")
                
                f.write("### 4. 投资顾问最终建议\n")
                f.write(result['investment_advice'])
            print(f"\n完整AutoGen多智能体分析报告已保存至: {report_file}")
            print(f"\n--- AutoGen多智能体协作优势体现 ---")
            print("1. 分工协作: 不同专业智能体负责不同分析领域")
            print("2. 知识传递: 分析结果在智能体间有序传递和深化")
            print("3. 综合决策: 投资顾问整合多方分析形成最终建议")
            print("4. 流程自动化: 用户只需提供股票代码，系统自动完成全流程分析")
            
    except Exception as e:
        print(f"执行过程中发生错误: {str(e)}")


if __name__ == "__main__":
    main()