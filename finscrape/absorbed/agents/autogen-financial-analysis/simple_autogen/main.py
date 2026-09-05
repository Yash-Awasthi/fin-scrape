"""
简约版AutoGen系统主入口文件
"""

import os
import sys
import logging
from pathlib import Path
import argparse
from typing import Dict, Any

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 确保可以导入simple_autogen_system
sys.path.insert(0, str(Path(__file__).parent))

# 导入核心系统
from simple_autogen_system import SimpleAutoGenSystem


def analyze_stock_command(args) -> None:
    """分析股票命令 - 展示AutoGen多智能体协作分析结果"""
    try:
        # 检查API密钥
        if not args.api_key:
            # 尝试从环境变量获取
            args.api_key = os.environ.get('OPENAI_API_KEY')
            if not args.api_key:
                logger.error("请提供OpenAI API密钥，通过参数或设置环境变量OPENAI_API_KEY")
                return

        # 创建系统实例
        system = SimpleAutoGenSystem(args.api_key)
        
        # 分析股票
        print(f"启动AutoGen多智能体协作分析 {args.symbol}...")
        result = system.analyze_stock(args.symbol)
        
        # 输出结果
        if 'error' in result:
            logger.error(f"分析失败: {result['error']}")
        else:
            print(f"\n===== {result['company_name']}({result['symbol']}) AutoGen多智能体协作分析结果 =====")
            print(f"分析日期: {result['analysis_date']}")
            print(f"AutoGen协作摘要: {result['autogen_collaboration_summary']}\n")
            
            # 打印财务指标
            print("\n--- 关键财务指标 (百分比) ---")
            financial = result['financial_metrics']
            for key, value in financial.items():
                if key in ['roe', 'roa', 'debt_ratio', 'gross_margin', 'net_margin']:
                    print(f"{key}: {value:.2f}%")
                else:
                    print(f"{key}: {value:.2f}")
            
            # 打印最终投资建议
            print(f"\n--- 投资顾问最终建议 ---")
            print(result['investment_advice'])
            
            # 如果需要保存到文件
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
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
                    for key, value in result['risk_metrics'].items():
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
                logger.info(f"完整AutoGen多智能体分析报告已保存到: {args.output}")
        
    except Exception as e:
        logger.error(f"执行分析时出错: {str(e)}")


def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(description='简约版AutoGen金融分析系统')
    
    # 子命令
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 分析股票命令
    analyze_parser = subparsers.add_parser('analyze', help='分析指定股票')
    analyze_parser.add_argument('symbol', help='股票代码，例如：AAPL')
    analyze_parser.add_argument('--api-key', '-k', help='OpenAI API密钥')
    analyze_parser.add_argument('--output', '-o', help='输出报告文件路径')
    
    # 显示帮助信息如果没有指定命令
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    # 解析参数
    args = parser.parse_args()
    
    # 执行相应命令
    if args.command == 'analyze':
        analyze_stock_command(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()