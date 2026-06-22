// Lightweight_mini-game
// 轻量级小游戏 —— 高铭聪
// 编码：GB2312

#include <bits/stdc++.h>
#include <windows.h>
#include <unistd.h>
#include <conio.h>
#include <stdlib.h>
using namespace std;
const int maxn = 55;

/*

公告：
1.2版本更新内容：
	西洋剑实装
	摇钱树实装
	新增游戏介绍
	修复了基础功能存在的BUG
	提高了不同机型的适配度 
	以及删除了Herobrine 
	
1.3版本更新内容:
    死亡机制修复
	添加了职业功能
	加入了职业“剑士”、“神行太保”
	加入了迅捷药水、盾
	加入了职业熟练度
	修复了以往诸多BUG
	以及删除了Herobrine 
	
1.31版本更新内容:
	职业、武器、金币数量可视化
	增加了301中控的适配度
	以及删除了Herobrine 
*/



/*
任务单：	
完成更多武器\机制 
*/

//[Header:Definition]
int G[maxn][maxn],n,box_mx,tree_mx = 2,box,tree;
short index = 0,op = 0,r = 0;
bool running = true,A[maxn][maxn],B[maxn][maxn],T[maxn][maxn];

//[Header:Tools]
struct TL{
	int id;
	/*
	大剑1
	西洋剑2 
	*/
	string name;
	int mia,mxa,am;//最小值,最大值,攻击容量 
	//方向偏移量
	bool phy,mag;//物伤·魔伤 
	int detx[25] = {0};//以朝向为x正轴，玩家位置为原点,玩家左向为y正轴
	int dety[25] = {0};
	/*e.g.
	o——>y
	|朝向下
	| 
	↓
	x 
	*/ 
}tl1,tl2;

//[Header:Professions]
struct PF{
	string name;
	int id;//1-剑士 2-弓手（未实装） 3-神行太保 4-天灾之下 5-法师 
	int suit = 0;//熟练度 
	int level = 0;//熟练等级 
	int add_dam;//各职业加伤
	int add_hpm;//各职业加血
	int add_mpm;//各职业加魔 
	
	int sut1 = 5,sut2 = 10,sut3 = 20;
	int sxtb_con = 10;
}pf1,pf2,pf3,pf4,pf5;

//[Header:Player]
struct pl{
	int id,att = 1,rod = 1;//id以及执行攻击操作次数以及操作次数 
	int hp,mxhp=20;
	int mp,mxmp=5;
	int mon = 10;
	map<pair<int,string>,int> items;
	int dx,dy;
	
	double res_phy_beg = 1,res_mag_beg = 1.5;//抗性药回复后的值 
	double res_phy = 1,res_mag = 1.5;//物抗·魔抗 
	int res_round = 0;//抗性药持续回合 
	bool shie = 0;//盾 
	
	TL at;
	PF ap;
	char dis = 'w';
}p1,p2,pt;//临时pt 

int los_id = 0;

//[Header:DateStructure]
struct dat_1{//攻击数据传回 
	int dem;//造成伤害
	int id;//受击对象 1-P1 2-P2
	int isTree;
};
struct dat_2{//效果数据传回 
	int dx;//
	int dy;//被命中目标偏移
	int xx;
	int yy;//主体位移 
	bool mov_ag;//再次移动效果触发 
	bool att_ag;//二次攻击判定效果触发 
};

pair<int,string> goods[15000];
bool ending = 0;//游戏结束 

//[Header:Function_define]
void empty_tips();
void color_print(int x,string s1,char s2);
void start_1();
void start_2();
void start_3();
void init();
int _rand(int beg,int end);
void map_creat();
void map_print();
void col_beg(int x);
void col_end();
void round();
bool pd_byd(int x,int y);
bool pd_ispl(int ax,int ay,int bx,int by);
bool pd_climb(int ax,int ay,int hmt);
bool pd_down(int ax,int ay,int hmt);
bool pd_death(pl w1,pl w2);
void pd_Atth(pl p_at);
pl market_run(pl p);
pl bag_print(pl pu);
void map_attack();
void turn(pl p,char ds);
void Ainit();
dat_1 Damage(pl p_at,pl p_bat);
dat_2 FlyMyPlayer(pl p_at,pl p_bat);
void Death(pl p_win,pl p_lose);
void Indro();
void SetColor(int r, int g, int b);


//[Header:Main_function]
int main(){
	/*srand((unsigned)time(NULL));
	thread printThread(start_1);
	_getch();
	index = 4;
	running = false;
	printThread.join();
	system("cls");*/
beginning:
	srand((unsigned)time(NULL)); // 初始化随机种子，消除rand卡顿
	start_2();
	start_3();
	while(true){
		round();
		if(ending){
			ending = 0;
			goto beginning;
		}
	}
	return 0;
}

//[Header:Function_content]
void empty_tips(){
/*0 = 黑色	1 = 蓝色	2 = 绿色	3 = 湖蓝色
4 = 红色	5 = 紫色	6 = 黄色	7 = 白色	8 = 灰色	9 = 亮蓝色
A=亮绿色	B=亮湖蓝色	C=亮红色	D=亮紫色	E=亮黄色	F=亮白色*/
}
void color_print(int x,string s1,char s2){//彩色输出
	SetConsoleTextAttribute(GetStdHandle(STD_OUTPUT_HANDLE),x);//前面数字代表底色，后面是字色 
	cout<<s1<<s2;
	SetConsoleTextAttribute(GetStdHandle(STD_OUTPUT_HANDLE),0x0F);
	return;
}
void SetColor(int r, int g, int b) {//RGB输出 
   HANDLE hConsole = GetStdHandle(STD_OUTPUT_HANDLE);
   std::cout << "\033[38;2;" << r << ";" << g << ";" << b << "m";
} 
void col_beg(int x){
	SetConsoleTextAttribute(GetStdHandle(STD_OUTPUT_HANDLE),x);
}
void col_end(){
	SetConsoleTextAttribute(GetStdHandle(STD_OUTPUT_HANDLE),0x0F);
}
void round(){
	r++;
	p1.rod = 1;
	p2.rod = 1;
	p1.att = 1;
	p2.att = 1;
	pl temp,oth;
	if(r%2==1)temp = p1,oth = p2;
	else temp = p2,oth = p1;
	char itm;
	bool move_ag = 0;
	map_print();
	cout << "\n\n";
	col_beg(0x0F);
choose:
	if(move_ag){
		cout << "现在是神行太保的额外回合！"; 
	}
	cout << "执行你的操作(ps:输入操作序号或wasd)：\n\n";
	col_end();
	if(r%2==1){
		col_beg(0x0C);
	}
	else col_beg(0x09);
	cout << "1-移动(w-a-s-d)  2-攻击  3-打开背包  4-商店\n";
	col_end();
	//itm = _getch();
	cin >> itm;
	int px,py;//下一步将会移动到的坐标
	if(itm=='2'){//攻击 
		if(!temp.att){
			cout << "这回合你不能再攻击了!\n";
			_sleep(1000);
			goto choose;
		}
		px = temp.dx,py = temp.dy;//现状保存匣() 
		system("cls");
		map_attack();
		cout << "\n\n请输入方向(w-a-s-d)\n";
		char dis = 'w';//朝向
		cin >> dis;
		temp.dis = dis;
		if(dis=='w'||dis=='a'||dis=='s'||dis=='d'){
			turn(temp,dis);
		}
		else {
			system("cls");
			map_print();
			goto choose;
		}
		system("cls");
		/*for(int i = 1;i <= n;i++){
			for(int j = 1;j <= n;j++){
				cout << A[i][j] <<' ';
			}
			cout << '\n';
		}*/
		system("cls");
		map_attack();
		cout <<"\n\n确定攻击？ 1-是  2-否\n\n";
		cin >> op;
		dat_1 infor_1;
		dat_2 infor_2;
		if(op==1){
			infor_1 = Damage(temp,oth);
			temp.rod --;
			temp.att --;
		}
		else {
			system("cls");
			map_print();
			goto choose;
		}
		/**/
		if(temp.ap.id == 1&&(temp.at.id==1||temp.at.id==2)){
			infor_1.dem += temp.ap.add_dam;
			temp.ap.suit++;
		}
		/**/
		system("cls");
		map_print();
		if(!infor_1.id&&!infor_1.isTree){
			cout << "\n\n打空啦！\n";
			_sleep(1000);
		}
		else if(infor_1.id==oth.id){
			//oth.hp -= infor_1.dem;
			int dam[50] = {0};
			int at_num = 0;
			if(temp.at.phy){
				if(oth.shie){
					infor_1.dem = (infor_1.dem>2?infor_1.dem-2:0);
				}
			}
			dam[++at_num] = infor_1.dem;
			//cout << infor_1.dem << '\n';
			infor_2 = FlyMyPlayer(temp,oth);
			int sl_dam = 0;
			bool sl = 0;
			int dam_s = 0;
			if(infor_2.att_ag){
				int dem_ag = _rand(temp.at.mia,temp.at.mxa);
				if(temp.at.phy){
					if(oth.shie){
						dem_ag = (dem_ag>2?dem_ag-2:0);
					}
				}
				dam[++at_num] = dem_ag;
			}
			for(int i = 1;i <= at_num;i++){
				oth.hp = (oth.hp - dam[i] >= 0) ? (oth.hp - dam[i]) : 0;
				dam_s += dam[i];
			}
			if(infor_2.dx != oth.dx||infor_2.dy != oth.dy){	
				if(!pd_down(oth.dx,oth.dy,G[infor_2.dy][infor_2.dx])){
					sl = 1;
					sl_dam = G[oth.dy][oth.dx]-G[infor_2.dy][infor_2.dx];
					oth.hp = (oth.hp - sl_dam >= 0) ? (oth.hp - sl_dam) : 0;
				}
				oth.dx = infor_2.dx;
				oth.dy = infor_2.dy;
			}
			if(infor_2.xx != temp.dx||infor_2.yy != temp.dy){
				temp.dx = infor_2.xx;
				temp.dy = infor_2.yy;
				if(r%2==1){
					p1 = temp;
					p2 = oth;
				}
				else {
					p2 = temp;
					p1 = oth;
				}
			}
			if(r%2==1){
				p1 = temp;
				p2 = oth;
			}
			else {
				p2 = temp;
				p1 = oth;
			}
			system("cls");
			map_print();
			cout << "\n\n命中！造成了 " << dam_s << " 点伤害";
			if(sl){
				cout << "并打飞了Ta";
				if(sl_dam){
					cout << "，顺带造成了 ";
					col_beg(0x0C);
					cout << sl_dam;//
					col_end();
					cout << " 点摔落伤害";
				}
			}
			cout << "!\n\n";
			if(infor_2.mov_ag){
				temp.rod ++;
				cout << "触发了 再次行动 的效果，本回合可以再移动一次！\n\n";
			}
			if(infor_2.att_ag){
				cout << "触发了 二段伤害 的效果，本次攻击再次判定！\n\n"; 
			}
			_sleep(1000);
		}
		if(infor_1.isTree){
			temp.mon += 20*infor_1.isTree;
			cout << "\n摇钱树摇啊摇，你获得了 ";
			col_beg(0x0E);
			cout << 20*infor_1.isTree;
			col_end();
			cout << " 个金币~\n\n";
			_sleep(1000);
		}
		if(r%2==1){
			p1 = temp;
			p2 = oth;
		}
		else {
			p2 = temp;
			p1 = oth;
		}
		pd_death(p1,p2);
		/*temp.dx = ux;
		temp.dy = uy;*/
		/*if(!pd_byd(temp.dx,temp.dy)){
			cout << "efddgdg!~*\n\n";
		}*/
	} 
	else if(itm=='3'){
		px = temp.dx,py = temp.dy;
		temp = bag_print(temp);
		if(r%2==1){
			p1 = temp;
			p2 = oth;
		}
		else {
			p2 = temp;
			p1 = oth;
		}
		if(temp.rod <= 0){
			system("cls");
			return;
		}
		system("cls");
		map_print();
		cout << "\n";
		goto choose;
	}
	else if(itm=='4'){
		temp = market_run(temp);
		system("cls");
		map_print();
		cout << "\n";
		goto choose;
	}  
	else{
		if(itm=='w'){
			px = temp.dx;
			py = temp.dy-1;
		}
		else if(itm=='a'){
			px = temp.dx-1;
			py = temp.dy;
		}
		else if(itm=='s'){
			px = temp.dx;
			py = temp.dy+1;
		}
		else if(itm=='d'){
			px = temp.dx+1;
			py = temp.dy;
		}
		else {
			system("cls");
			map_print();
			cout << "\n你这啥？？重来！\n\n" ; 
			goto choose;
		}
		if(!pd_ispl(px,py,oth.dx,oth.dy)){
			system("cls");
			map_print();
			cout << "\n踹到人了！\n\n";
			goto choose;
		}
		if(!pd_byd(px,py)){
			system("cls");
			map_print();
			cout << '\n';
			string bydzf[5] = {"\n越权访问！\n\n","\n前面的区域以后再来探索吧！\n\n","\n法无授权不可为！\n\n"};
			cout << bydzf[_rand(0,2)];
			goto choose;
		}
		if(!pd_climb(temp.dx,temp.dy,G[py][px])){
			system("cls");
			map_print();
			cout << '\n';
			if(temp.items[make_pair(1,"梯子")]<=0){
				cout << "你需要一把梯子！\n\n"; 
				goto choose;
			}
			else{
				cout << "是否使用梯子？\n1-是    2-否\n\n";
				cin >> op;
				if(op==1){
					temp.items[make_pair(1,"梯子")]--;
					temp.dx = px;
					temp.dy = py;//
					system("cls");
					map_print();
				}
				else goto choose;
			}
		}
		if(!pd_down(temp.dx,temp.dy,G[py][px])){
			system("cls");
			map_print();
			cout << '\n';
			if(temp.items[make_pair(2,"绳子")]<=0){
				cout << "你没有绳子！是否直接下山？\n1-是    2-否\n\n"; 
				cin >> op;
				if(op==1){
					int dh = G[temp.dy][temp.dx]-G[py][px];
					temp.hp = (temp.hp-dh>=0?temp.hp-dh:0);//
					cout << "\n你受到了 ";
					col_beg(0x0C);
					cout << G[temp.dy][temp.dx]-G[py][px];//
					col_end();
					cout << " 点摔落伤害！\n\n";
					temp.dx = px;
					temp.dy = py;
					if(r%2==1){
						p1 = temp;
						p2 = oth;
					}
					else {
						p2 = temp;
						p1 = oth;
					}
					_sleep(1000);
				}
				else goto choose;
			}
			else{
				cout << "是否使用绳子？\n1-是    2-否\n\n";
				cin >> op;
				if(op==1){
					temp.items[make_pair(2,"绳子")]--;
					temp.dx = px;
					temp.dy = py;
					system("cls");
					map_print();
				}
				else{
					system("cls");
					map_print();
					cout << "\n是否直接下山？\n1-是    2-否\n\n";
					cin >> op;
					if(op==1){
						int dh = G[temp.dy][temp.dx]-G[py][px];
						temp.hp = (temp.hp - dh >= 0) ? (temp.hp - dh) : 0;//
						cout << "\n你受到了 ";
						col_beg(0x0C);
						cout << G[temp.dy][temp.dx]-G[py][px];//
						col_end();
						cout << " 点摔落伤害！\n\n";
						temp.dx = px;
						temp.dy = py;
						if(r%2==1){
							p1 = temp;
							p2 = oth;
						}
						else {
							p2 = temp;
							p1 = oth;
						}
						_sleep(1000);
					}
					else goto choose;
				}
			}
			if(r%2==1){
				p1 = temp;
				p2 = oth;
			}
				else {
				p2 = temp;
				p1 = oth;
			}
			pd_death(p1,p2);
		}
		temp.rod--;	
		temp.dx = px;
		temp.dy = py;
		if(r%2==1){
			p1 = temp;
			p2 = oth;
		}
		else {
			p2 = temp;
			p1 = oth;
		}
		system("cls");
		map_print();
	} 
	int rad_sxtb = _rand(0,temp.ap.sxtb_con);
	if(temp.ap.id == 3&&!move_ag&&rad_sxtb==1){
		temp.ap.suit++;
		if(r%2==1){
			p1 = temp;
			p2 = oth;
		}
		else {
			p2 = temp;
			p1 = oth;
		}
		system("cls");
		map_print();
		cout <<'\n';
		move_ag = 1;
		temp.rod++;
	}
	if(temp.rod)goto choose;
	
	if((temp.ap.suit>=temp.ap.sut1&&temp.ap.level==0)||
	   (temp.ap.suit>=temp.ap.sut2&&temp.ap.level==1)||
	   (temp.ap.suit>=temp.ap.sut3&&temp.ap.level==2)){
		if(temp.ap.level==0){
			cout << "\n你对你的职业开始逐渐上手。\n";
			temp.ap.level = 1;
			
			temp.ap.add_dam++;
			temp.ap.add_hpm++;
			temp.ap.add_mpm++;
			temp.ap.sxtb_con = 8;
			_sleep(1000);
		}
		else if(temp.ap.level==1){
			cout << "\n你对你的职业愈发地熟练了。\n";
			temp.ap.level = 2;
			
			temp.ap.add_dam++;
			temp.ap.add_hpm++;
			temp.ap.add_mpm++;
			temp.ap.sxtb_con = 6;
			_sleep(1000);
		}
		else if(temp.ap.level==2){
			cout << "\n你对你的职业已然炉火纯青。\n";
			temp.ap.level = 3;
			
			temp.ap.add_dam++;
			temp.ap.add_hpm+=3;
			temp.ap.add_mpm+=3;
			temp.ap.sxtb_con = 3;
			_sleep(1000);
		} 
	}
	
	/*temp.dx = px;
	temp.dy = py;*/
	if(r%2==1){
		p1 = temp;
		p2 = oth;
	}
	else {
		p2 = temp;
		p1 = oth;
	}
	system("cls");
}
bool pd_byd(int ax,int ay){
	if(ax < 1||ay < 1||ax > n||ay > n){
		return false;
	}
	else return true;
}
bool pd_ispl(int ax,int ay,int bx,int by){
	if(ax==bx&&ay==by){
		return false;
	}
	else return true;
}
bool pd_climb(int ax,int ay,int hmt){
	if(hmt-G[ay][ax]>=2){//大于等于2的高度需要梯子 
		return false;
	}
	return true;
}
bool pd_down(int ax,int ay,int hmt){
	if(G[ay][ax]-hmt>=2){//大于等于2的高度需要绳子 
		return false;
	}
	return true;
}
bool pd_death(pl w1,pl w2){
	if(w1.hp <= 0||w2.hp <= 0){
		if(w1.hp <= 0){
			los_id = w1.id;
			Death(w2,w1);
		}
		else if(w2.hp <= 0){
			los_id = w2.id;
			Death(w1,w2);
		}
		return true; 
	}
	return false;
}
void start_1(){
	/*while(index!=4&&running){
		if(index==0){
			this_thread::sleep_for(chrono::seconds(1));
			cout << "n";
			this_thread::sleep_for(chrono::seconds(1));
			cout << "i";
			this_thread::sleep_for(chrono::seconds(1));
		}
		if(index==1){
			system("cls");
			cout << "你";
			this_thread::sleep_for(chrono::seconds(1));
			cout << "h";
			this_thread::sleep_for(chrono::seconds(1));
			cout << "a";
			this_thread::sleep_for(chrono::seconds(1));
			cout << "p";
			this_thread::sleep_for(chrono::seconds(1));
		}
		if(index==2){
			system("cls");
			cout << "你ha";
			this_thread::sleep_for(chrono::seconds(1));
			cout << "o";
			this_thread::sleep_for(chrono::seconds(1));
		}
		if(index==3){
			system("cls");
			cout << "你好";
			this_thread::sleep_for(chrono::seconds(1));
			cout << "!";
			this_thread::sleep_for(chrono::seconds(2));
			system("cls");
			cout <<"		 -按任意键开始游戏-";
		}
		index++;
	}	*/
//system("cls");
}
void start_2(){
	/*index = 0;
	system("cls");
	string s1 = "欢迎来到……";
	while(index!=13){
		_sleep(100);
		color_print(0x0B,"",s1[index]);
		index++;
	}
	_sleep(1000);
	system("cls");
	color_print(0x0B,"《轻量级小游戏》",' ');
	_sleep(1000);
	system("cls");
	cout << "（逃掉了……）";
	sleep(1);*/
	system("cls");
	color_print(0x0B,"                   -轻量级小游戏-\n\n",' ');
	cout << "选择游戏模式：\n\n"; 
	color_print(0x09,"   1-对战模式  ",' '); 
	color_print(0x0C,"  2-游戏介绍  ",' '); 
	color_print(0x0F,"  3-设置  ",' '); 
	color_print(0x08,"  4-敬请期待...\n",' '); 
}
void start_3(){
	cin >> op;
	//———//
	if(op==1){
		cout << "（其实对战模式也没开发好（））";
		_sleep(300); 
		system("cls");
		cout << "		选择地图大小：\na.10*10(轻量级=P)   b.25*25(大地图=D)   c.50*50(不建议XD)\n";
		op = _getch();
		// - - - //
		if(op=='a')n = 10,tree_mx = 2;
		else if(op=='b')n = 25,tree_mx = 5;
		else if(op=='c')n = 50,tree_mx = 10;
		else n = 10;
		init();
		system("cls");
		cout << "       P1:选择职业：\n1.剑士\n2.弓手\n3.神行太保\n4.天灾之下\n5.法师\n";
		cin >> op;
		switch(op){
			case 1:
				p1.ap = pf1;
				break;
			case 2:
				p1.ap = pf2;
				break;
			case 3:
				p1.ap = pf3;
				break;
			case 4:
				p1.ap = pf4;
				break;
			case 5:
				p1.ap = pf5;
				break;
		}
		cout << "       P2:选择职业：\n1.剑士\n2.弓手\n3.神行太保\n4.天灾之下\n5.法师\n";
		cin >> op;
		switch(op){
			case 1:
				p2.ap = pf1;
				break;
			case 2:
				p2.ap = pf2;
				break;
			case 3:
				p2.ap = pf3;
				break;
			case 4:
				p2.ap = pf4;
				break;
			case 5:
				p2.ap = pf5;
				break;
		}
		cout << "       P1：选择初始武器: \n1.大剑\n2.西洋剑\n";
		cin >> op;
		switch(op){
			case 1:
				p1.at = tl1;
				break;
			case 2:
				p1.at = tl2;
				break;
		}
		cout << "       P2：选择初始武器: \n1.大剑\n2.西洋剑\n";
		cin >> op;
		switch(op){
			case 1:
				p2.at = tl1;
				break;
			case 2:
				p2.at = tl2;
				break;
		}
		system("cls");
	}
	else if(op==2){
		Indro();
		cin >> op;
	}
}
void Indro(){
	int r = 0,g = 0,b = 0; 
	system("cls"); 
	color_print(0x0B,"《轻量级小游戏》介绍\n\n",' ');
	cout << "你好，这是该小游戏的介绍！\n\n";
	cout << R"(一、对战模式
  (1)目标
  
    目标就是击败对方，取得战斗的胜利！在这个过程中可以使用各种方法，例如：获取各式各样的武器、 
   在商城购买各种装备或道具，以及运用智慧和策略等等
    
  (2)机制
  
    移动/攻击方向：w↑ a← s↓ d→
    金币：金币作为游戏内的基本货币，可以通过几种方式获取：
	 1.每5回合+2
	 2.打开宝箱获取
	 3.地图上刷新摇钱树，攻击后消失，+20
	 4.命中对方
	 5.更多其他途径……
   伤害类型：游戏内有 物理伤害 和 法术伤害，不同的武器可能有不同的伤害类型。
   抗性：每个玩家有 物理抗性（初始 1.0）和法术抗性（初始 0.5），最后受到的伤害（摔落除外） 
	会 乘上该数值（向下取整）	 
   武器：不同的武器有不同的效果，一名玩家 仅能装备一把武器 ，更换武器后原武器不会被丢弃，未
	装备的武器可以在 背包 中进行装备，武器详情请见“武器”。
   职业：不同的职业有不同的效果，详见“职业”。 
   地图：地图上有几种地块,地块上的数字表示高度
     0.红色(P1)/蓝色(P2) 表示 玩家 所在位置 
     1.高度为0的 地面 呈棕色
	 2.有高度(>0)的 山 呈绿色，登上 高度差 >2的山需要梯子，走下 高度差 >2的山需要绳子，否则
	  将受等同于高度差的 摔落伤害  
	 3.宝箱 呈黄色，会随机刷新在山上，需要钥匙打开
	 4.摇钱树 呈 橙色，会周期性刷新在地面上，攻击以获取金币 
二、设置
   设置中可以调整某些初始数值，或者ban某些武器/物品 
三、武器
四、职业
五、商城
六、宝箱)";
	cin >> op;
	system("cls");
}

void init(){
	los_id = 0;
	
	//p1 = {.id = 1,.hp = p1.mxhp,.mp = p1.mxmp,.dx = 1,.dy = 1};
	p1.id = 1;
	p1.hp = p1.mxhp;
	p1.mp = p1.mxmp;
	p1.dx = 1;
	p1.dy = 1;
	p1.items[make_pair(1,"梯子")] = 1;
	p1.items[make_pair(2,"绳子")] = 1;
	//p2 = pl{.id = 2,.hp = p2.mxhp,.mp = p2.mxmp,.dx = n,.dy = n};
	p2.id = 2;
	p2.hp = p2.mxhp;
	p2.mp = p2.mxmp;
	p2.dx = n;
	p2.dy = n;
	p2.items[make_pair(1,"梯子")] = 1;
	p2.items[make_pair(2,"绳子")] = 1;
	
	//
	int atsize_x_1[] = {1,2};
	int atsize_y_1[] = {0};
	//tl1 = {1,"dajian",1,2,2,1,0};
	tl1.id = 1,tl1.name = "大剑",tl1.mia = 1,tl1.mxa = 2,tl1.am = 2,tl1.phy = 1,tl1.mag = 0;
	std::copy(atsize_x_1,atsize_x_1+2,tl1.detx);
	//std::copy(atsize_y_1,atsize_y_1+2,tl1.dety);
	//tl1.detx[] = {1,2};像左边这样写是错误的XD 
	//tl1.dety[] = {0};
	//tl2 = {2,"xiyangjian",0,2,2,1,0};
	tl2.id = 2,tl2.name = "西洋剑",tl2.mia = 0,tl2.mxa = 2,tl2.am = 2,tl2.phy = 1,tl2.mag = 0;
	std::copy(atsize_x_1,atsize_x_1+2,tl2.detx);
	//std::copy(atsize_y_1,atsize_y_1+2,tl1.dety);
	//tl2.detx[] = {1,2};
	//tl2.dety[] = {0};
	//
	map_creat();
	//
	
	//职业
	pf1.name = "剑士";
	pf2.name = "弓手";
	pf3.name = "神行太保";
	pf4.name = "天灾之下";
	pf5.name = "法师";

	pf1.id = 1;
	pf2.id = 2;
	pf3.id = 3;
	pf4.id = 4;
	pf5.id = 5;
	
	pf1.add_dam = 1;
	pf2.add_dam = 1;
	pf5.add_dam = 1;
	
	//商店
	goods[1] = make_pair(1,"梯子");
	goods[2] = make_pair(2,"绳子");
	goods[3] = make_pair(3,"HP药");
	goods[4] = make_pair(4,"MP药");
	goods[5] = make_pair(5,"抗性药水");
	goods[6] = make_pair(6,"迅捷药水");
	goods[7] = make_pair(7,"盾");
	
	/*p1.at = tl2;
	p2.at = tl2;*/
	
}
void map_creat(){
	for(int i = 1;i <= n;i++){
		for(int j = 1;j <= n;j++){
			index = _rand(0,3);
			if(index != 0)continue;
			else G[i][j] = _rand(1,9);
		}
	}
}

void map_print(){
	if(!tree){
		int tree_t = tree_mx;
		tree = tree_mx; 
		int cnt = 0;
		while(tree_t){
			int tx = _rand(1,n);
			int ty = _rand(1,n);
			if(!G[ty][tx]&&p1.dx!=tx&&p1.dy!=ty&&p2.dx!=tx&&p2.dy!=ty&&!T[ty][tx]){
				T[ty][tx] = 1;
				tree_t--;
			}
		}
		/*while(tree_t&&cnt<=n*n*2){
			for(int i = 1;i <= n;i++){
				for(int j = 1;j <= n;j++){
					if(!G[i][j]&&(p1.dx!=j&&p1.dy!=i)&&(p2.dx!=j&&p2.dy!=i)){
						int temp = _rand(0,5);
						if(temp==3){
							T[i][j] = 1;
							tree_t--;
							tree++;
						}
					}
					cnt++;
				}
			}
		}*/
	}
	int h1 = int(p1.hp/4);
	int m1 = int(p1.mp/1);
	int h2 = int(p2.hp/4);
	int m2 = int(p2.mp/1);
	int r = 0,g = 0,b = 0;
	for(int i = 1;i <= n;i++){
		for(int j = 1;j <= n;j++){
			if(j==p1.dx&&i==p1.dy){
				col_beg(0x04);
				cout << G[i][j] << ' ';
				col_end();
				continue;
			}
			if(j==p2.dx&&i==p2.dy){
				col_beg(0x09);
				cout << G[i][j] << ' ';
				col_end();
				continue;
			}
			if(G[i][j]==0){
				if(!T[i][j]){
					col_beg(0x06);
					cout << G[i][j] << ' ';
					col_end();
				}
				else {
					SetColor(246,246,190);
					cout << "T ";
					SetColor(255,255,255);
				}
			}
			else{
				col_beg(0x0A);
				cout << G[i][j] << ' ';
				col_end();
			}
		}
		if(i==2){//以下皆是视觉效果 
			col_beg(0x04);
			cout << "	P1";
			col_end();
			cout << ":" << p1.ap.name << "lv."<<p1.ap.level<<" + " << p1.at.name;
			col_beg(0x0E);
			cout << "  金币";
			col_end();
			cout << ":" << p1.mon;
		}
		if(i==3){
			cout << "	HP:";
			if(h1>3)col_beg(0xAA);
			if(h1==2||h1==3)col_beg(0xEE);
			if(h1<2)col_beg(0xCC);
			while(h1){
				cout << "   ";
				h1--;
			}
			if(p1.hp>int(p1.mxhp/5*3))col_beg(0x0A);
			if(p1.hp>=int(p1.mxhp/5*2)&&p1.hp<=int(p1.mxhp/5*3))col_beg(0x0E);
			if(p1.hp<int(p1.mxhp/5*2))col_beg(0x0C);
			cout << " ";
			cout << p1.hp;
			cout << " ";
			col_end();
			cout << "/ " << p1.mxhp;
		}
		if(i==4){
			cout << "	MP:";
			col_beg(0x99);
			while(m1){
				cout << "   ";
				m1--;
			}
			col_beg(0x09);
			cout << " ";
			cout << p1.mp;
			cout << " ";
			col_end();
			cout << "/ " << p1.mxmp;
		}
		if(i==7){
			col_beg(0x09);
			cout << "	P2";
			col_end();
			cout << ":" << p2.ap.name << "lv."<<p2.ap.level<<" + " << p2.at.name;
			col_beg(0x0E);
			cout << "  金币";
			col_end();
			cout << ":" << p2.mon;
		}
		if(i==8){
			cout << "	HP:";
			if(h2>3)col_beg(0xAA);
			if(h2==2||h2==3)col_beg(0xEE);
			if(h2<2)col_beg(0xCC);
			while(h2){
				cout << "   ";
				h2--;
			}
			if(p2.hp>int(p2.mxhp/5*3))col_beg(0x0A);
			if(p2.hp<=int(p2.mxhp/5*3)&&p2.hp>=int(p2.mxhp/5*2))col_beg(0x0E);
			if(p2.hp<int(p2.mxhp/5*2))col_beg(0x0C);
			cout << " ";
			cout << p2.hp;
			cout << " ";
			col_end();
			cout << "/ " << p2.mxhp;
		}
		if(i==9){
			cout << "	MP:";
			col_beg(0x99);
			while(m2){
				cout << "   ";
				m2--;
			}
			col_beg(0x09);
			cout << " ";
			cout << p2.mp;
			cout << " ";
			col_end();
			cout << "/ " << p2.mxmp;
		}//到此皆为视觉效果 
		cout << "\n";
	}
	/*cout << "\n\n" << p1.dx << " " << p1.dy  << " " << G[p1.dy][p1.dx]<< "\n" << p2.dx << " " << p2.dy << " " << G[p2.dy][p2.dx] << "\n";
	cout << p1.lap <<" "<<p1.rop << "\n";
	cout <<p2.lap<<' '<<p2.rop<<'\n';*/
}
int _rand(int beg,int end){//随机数 
	int dif=end-beg+1;
	return rand()%dif+beg;
}
pl market_run(pl p){
	system("cls");
	int op1,op2,pri,tot;
	printf("====================商店====================\n"
		   " 品 名      	  效   果         	  价 钱	\n" 
		   "1.梯子*1     	   上山                 1   \n"
		   "2.绳子*1     	   下山                 1   \n"
		   "3.HP药*1     	使用后+2HP              5   \n"
		   "4.MP药*1     	使用后+1MP              5   \n"
		   "5.抗性药水*1 	使用后全抗性变为0.5     20  \n"
		   "6.迅捷药水*1    使用后能多行动1次       15  \n"
		   "7.盾*1      减免2点物理伤害(不可叠加)   50  \n"
		   "\n\n"); 
buy:
	cout << "请输入要购买的商品:";
	cin >> op1;
	switch(op1){//价格调整 
		case 1:
			pri = 1;
			break;
		case 2:
			pri = 1;
			break;
		case 3:
			pri = 5;
			break;
		case 4:
			pri = 5;
			break;
		case 5:
			pri = 20;
			break;
		case 6:
			pri = 15;
			break;
		case 7:
			pri = 50;
			break;
	}
	cout << "\n请输入要购买的数量:";
	cin >> op2;
	cout << "\n现有金币数:";
	col_beg(0x0E);
	cout << p.mon << "\n";
	col_end();
	cout << "\n金币计算：" << op2 << " x " << pri << " = "; 
	tot = op2*pri;
	if(tot<=p.mon){
		col_beg(0x0A);
		cout << tot << "\n";
		_sleep(500);
		cout << "确定要购买吗? 你将会剩余：";
		col_beg(0x0E);
		cout << p.mon - tot;
		col_end();
		cout << " 枚金币\n1-是  2-否\n\n";
		cin >> pri;
		if(pri==1){
			p.mon-=tot; 
			p.items[goods[op1]]+=op2;
			cout << "购买成功！";
			_sleep(2000); 
			return p;
		}
		else {
			cout << "那太遗憾了！";
			_sleep(2000);
			return p; 
		}
	}
	else {
		col_beg(0x0C);
		cout << tot << "\n";
		col_end();
		_sleep(1000);
		cout << "你买不起啊！\n";
		_sleep(2000);
		return p;
	}
}
pl bag_print(pl pu){
	pl p = pu;
	system("cls"); 
	col_beg(0x0E);
	printf("========*◆王之宝库◆*========\n");
	col_end();
	for(int i = 1;i <= p.items.size();i++){
		if(p.items[goods[i]]){
			cout << goods[i].second << ":" << p.items[goods[i]] << "\n";
		}
	}
	cout << "输入物品名称(中文)以使用(或输入其他字符以退出):\n";
	string itm;
	cin >> itm;
	if(itm=="HP药"&&p.items[goods[3]]){
		p.hp+=2;
		p.rod --; 
		p.items[goods[3]]--;
		if(p.hp>p.mxhp)p.hp = p.mxhp;
		col_beg(0x0A);
		cout <<"成功回复了 2 点生命值！\n";
		col_end();
		_sleep(1000);
	}
	if(itm=="MP药"&&p.items[goods[4]]){
		p.mp+=1;
		p.rod --;
		p.items[goods[4]]--;
		if(p.mp>p.mxmp)p.mp = p.mxmp;
		col_beg(0x09);
		cout <<"成功回复了 1 点魔力！\n";
		col_end();
		_sleep(1000);
	}
	if(itm=="抗性药水"&&p.items[goods[5]]){
		p.res_phy = 0.5;
		p.res_mag = 0.5;
		p.res_round = 4; 
		//p.rod --;//看情况，如果抗性药太过超模就削 
		p.items[goods[5]]--;
		col_beg(0x0F);
		cout <<"全抗变为0.5！持续4个自身回合\n";
		col_end();
		_sleep(1000);
	}
	if(itm=="迅捷药水"&&p.items[goods[6]]){
		p.rod++;
		SetColor(0,238,187);
		cout << "本回合可以额外行动一次！\n";
		SetColor(255,255,255);
		_sleep(1000);
	}
	if(itm=="盾"&&p.items[goods[7]]){
		p.shie = 1;
		SetColor(242,145,70);
		cout << "获得物理伤害减免！\n";
		SetColor(255,255,255);
		_sleep(1000);
	}
	return p;
}
void map_attack(){
	for(int i = 1;i <= n;i++){
		for(int j = 1;j <= n;j++){
			if(A[i][j]){
				if(j==p1.dx&&i==p1.dy){
					col_beg(0xF4);
					cout << G[i][j] << "   ";
					col_end();
					continue;
				}
				if(j==p2.dx&&i==p2.dy){
					col_beg(0xF9);
					cout << G[i][j] << "   ";
					col_end();
					continue;
				}
				if(G[i][j]==0){
					if(!T[i][j]){
						col_beg(0xF6);
						cout << G[i][j] << "   ";
						col_end();
					}
					else {
						col_beg(0xF6);
						cout << "T   ";
						col_end();
					}
				}
				else{
					col_beg(0xFA);
					cout << G[i][j] << "   ";
					col_end();
				}
			}
			else{
				if(j==p1.dx&&i==p1.dy){
					col_beg(0x04);
					cout << G[i][j] << "   ";
					col_end();
					continue;
				}
				if(j==p2.dx&&i==p2.dy){
					col_beg(0x09);
					cout << G[i][j] << "   ";
					col_end();
					continue;
				}
				if(G[i][j]==0){
					if(!T[i][j]){
						col_beg(0x06);
						cout << G[i][j] << "   ";
						col_end();
					}
					else {
						SetColor(246,246,190);
						cout << "T   ";
						SetColor(255,255,255);
					}
				}
				else{
					col_beg(0x0A);
					cout << G[i][j] << "   ";
					col_end();
				}
			}
		}
		cout << "\n\n";
	}
}
void turn(pl p,char ds){
	Ainit();
	int tx = p.dx,ty = p.dy;//玩家位置 
	if(ds=='w'){
		for(int k = 0;k < p.at.am;k++){
			if(pd_byd(tx-p.at.dety[k],ty-p.at.detx[k])){
				A[ty-p.at.detx[k]][tx-p.at.dety[k]] = 1;
			}
			else return;
		}
	}
	else if(ds=='d'){
		for(int k = 0;k < p.at.am;k++){
			if(pd_byd(tx+p.at.detx[k],ty-p.at.dety[k])){
				A[ty-p.at.dety[k]][tx+p.at.detx[k]] = 1;
			}
			else return;
		}
	}
	else if(ds=='s'){
		for(int k = 0;k < p.at.am;k++){
			if(pd_byd(tx+p.at.dety[k],ty+p.at.detx[k])){
				A[ty+p.at.detx[k]][tx+p.at.dety[k]] = 1;
			}
			else return;
		}
	}
	else if(ds=='a'){
		for(int k = 0;k < p.at.am;k++){
			if(pd_byd(tx-p.at.detx[k],ty+p.at.dety[k])){
				A[ty+p.at.dety[k]][tx-p.at.detx[k]] = 1;
			}
			else return;
		}
	}
	pd_Atth(p);
	//
}
void Ainit(){
	for(int i = 1;i <= n;i++){
		for(int j = 1;j <= n;j++){
			A[i][j] = 0;
		}
	}
}
dat_1 Damage(pl p_at,pl p_bat){
	dat_1 mRNA = {0,0,0};
	for(int i = 1;i <= n;i++){
		for(int j = 1;j <= n;j++){
			if(A[i][j]){
				if(i==p_bat.dy&&j==p_bat.dx){
					mRNA.dem = _rand(p_at.at.mia,p_at.at.mxa);
					if(p_at.at.phy)mRNA.dem = int(mRNA.dem*p_at.res_phy);
					else mRNA.dem = int(mRNA.dem*p_at.res_mag);
					mRNA.id = p_bat.id;
				}
				if(T[i][j]){
					T[i][j] = 0;
					tree--;
					mRNA.isTree ++;
				}
			}
		}
	}
	Ainit();
	return mRNA;
}
void pd_Atth(pl p_at){
	int tid = p_at.at.id;
	int h = G[p_at.dy][p_at.dx];
	int ux = p_at.dx,uy = p_at.dy;
	bool vis[maxn][maxn] = {0};
	queue<pair<int,int>> q;//first-y,second-x
	int g[10] = {1,0,-1,0};//偏移量 
	q.push(make_pair(uy,ux));
	vis[uy][ux] = 1;
	/*while(!q.empty()){
		pair<int,int> cur;
		cur = q.front();
		int nx = cur.second,ny = cur.first;
		q.pop();
		for(int i = 0;i < 4;i++){
			for(int j = 0;j < 4;j++){
				if(A[ny+g[i]][nx+g[j]]&&!vis[ny+g[i]][nx+g[j]]){
					//bool ks = 0;
					vis[ny+g[i]][nx+g[j]] = 1;
					if(tid==1||tid==2){//普通近战武器板子 BFS
						if(fabs(G[ny+g[i]][nx+g[j]]-h)>1){//高度差大于1 
							A[ny+g[i]][nx+g[j]] = 0;
							//ks = 1;
						}
					}
					q.push(make_pair(ny+g[i],nx+g[j]));
					//if(ks==0)q.push(make_pair(ny+g[i],nx+g[j]));考不考虑隔山打不到的功能？(2026.5.17) 
				}
			}
		}
	}*/
	//使用BFS寻路 还不如直接暴力，还会漏点( 
	if(tid==1||tid==2){
		for(int i = 1;i <= n;i++){
			for(int j = 1;j <= n;j++){
				if(fabs(G[i][j]-h)>1){//高度差大于1 
					A[i][j] = 0;
					//ks = 1;
				}
			}
		}
	}
}
dat_2 FlyMyPlayer(pl p_at,pl p_bat){
	int tid = p_at.at.id;
	int d_at = p_at.dis;
	int pe = 0;
	dat_2 tol = {p_bat.dx,p_bat.dy,p_at.dx,p_at.dy};
	if(tid==1){//大剑 
		pe = _rand(0,1);
		if(d_at=='w'||d_at=='s'){
			if(pe==0){
				if((pd_climb(p_bat.dx-1,p_bat.dy,G[p_bat.dy][p_bat.dx])
					/*||pd_down(p_bat.dx-1,p_bat.dy,G[p_bat.dy][p_bat.dx]*/)
					&&pd_byd(p_bat.dx-1,p_bat.dy))tol.dx = p_bat.dx-1;
			}
			else {
				if((pd_climb(p_bat.dx+1,p_bat.dy,G[p_bat.dy][p_bat.dx])
					/*||pd_down(p_bat.dx+1,p_bat.dy,G[p_bat.dy][p_bat.dx]*/)
					&&pd_byd(p_bat.dx+1,p_bat.dy))tol.dx = p_bat.dx+1;
			}		
		}
		if(d_at=='a'||d_at=='d'){
			if(pe==0){
				if((pd_climb(p_bat.dx,p_bat.dy-1,G[p_bat.dy][p_bat.dx])
					/*||pd_down(p_bat.dx,p_bat.dy-1,G[p_bat.dy][p_bat.dx]*/)
					&&pd_byd(p_bat.dx,p_bat.dy-1))tol.dy = p_bat.dy-1;
			}
			else {
				if((pd_climb(p_bat.dx,p_bat.dy+1,G[p_bat.dy][p_bat.dx])
					/*||pd_down(p_bat.dx,p_bat.dy+1,G[p_bat.dy][p_bat.dx]*/)
					&&pd_byd(p_bat.dx,p_bat.dy+1))tol.dy = p_bat.dy+1;
			}		
		}
	}
	if(tid==2){//西洋剑 
		pe = _rand(0,4);
		if(d_at=='w'){
			if((pd_climb(p_at.dx,p_at.dy+1,G[p_at.dy][p_at.dx])
				&&pd_down(p_at.dx,p_at.dy+1,G[p_at.dy][p_at.dx])
				&&pd_byd(p_at.dx,p_at.dy+1)))tol.yy = p_at.dy+1;
		}
		else if(d_at=='s'){
			if((pd_climb(p_at.dx,p_at.dy-1,G[p_at.dy][p_at.dx])
				&&pd_down(p_at.dx,p_at.dy-1,G[p_at.dy][p_at.dx])
				&&pd_byd(p_at.dx,p_at.dy-1)))tol.yy = p_at.dy-1;
		}
		else if(d_at=='a'){
			if((pd_climb(p_at.dx+1,p_at.dy,G[p_at.dy][p_at.dx])
				&&pd_down(p_at.dx+1,p_at.dy,G[p_at.dy][p_at.dx])
				&&pd_byd(p_at.dx+1,p_at.dy)))tol.xx = p_at.dx+1;
		}
		else {
			if((pd_climb(p_at.dx-1,p_at.dy,G[p_at.dy][p_at.dx])
				&&pd_down(p_at.dx-1,p_at.dy,G[p_at.dy][p_at.dx])
				&&pd_byd(p_at.dx-1,p_at.dy)))tol.xx = p_at.dx-1;
		}
		if(pe==3){
			tol.att_ag = 1;
		}
	}
	return tol;
}
void Death(pl p_win,pl p_lose){
	//map_print();
	_sleep(1000);
	system("cls");
	cout << "\nP"<<p_win.id<<"获得了胜利！让我们恭喜Ta！\n\n";
	_sleep(2000);
	cout << "\n接下来将回到开始界面！";
	ending = 1;
	_sleep(2000);
}
