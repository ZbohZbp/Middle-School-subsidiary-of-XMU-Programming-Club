# Energy_duel
# 能量博弈2 —— 陈劲龙
# pyinstaller -F --hidden-import=pygame --paths C:\Users\xiaot\myenv\Lib\site-packages --add-data "audio;audio" --add-data "game;game" main.py

"""能量博弈 - 双人回合制对战游戏启动器"""
from game.ui import start_game

if __name__ == "__main__":
    start_game()
