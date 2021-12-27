import curses
import curses.ascii
import random

UP = 0
DOWN = 1
DIV = 2

ACTION_ROLL = 0
ACTION_BUY = 1
ACTION_SELL = 2

def rgb(r, g, b):
    return r * 36 + g * 6 + b + 17

stocks = ["grain", "industrial", "bonds", "oil", "silver", "gold"]


num_stocks = len(stocks)

values = {stock: 100 for stock in stocks}
actions = ["up", "down", "div"]


class Player:
    def __init__(self, name, money=5000):
        self.name = name
        self.money = money
        self.holdings = {stock: 0 for stock in stocks}

class Game:
    def __init__(self, stdscr):
        self.get_players()
        self.num_players = len(self.players)
        self.values = {stock: 100 for stock in stocks}
        self.current_player = 0
        self.current_stock  = 0
        self.current_action = ACTION_ROLL
        self.current_buy = 0
        self.current_value = 0
        self.do_action = False

        self.stdscr       = stdscr
        self.board_win    = curses.newwin(len(stocks) + 2, 60, 0, 0)
        self.holdings_win = curses.newwin(len(stocks) + 6, 60, self.board_win.getmaxyx()[0], 0)
        self.action_win   = curses.newwin(curses.LINES - num_stocks * 2 - 7 - 1, 60, self.holdings_win.getmaxyx()[0] + self.board_win.getmaxyx()[0], 0)
        self.log_win      = curses.newwin(curses.LINES, curses.COLS - 60, 0, 60)
        self.log_win.scrollok(True)
        
        self.main()

    def roll(self):
        stock  = random.randint(0, num_stocks - 1)
        stock  = stocks[stock]
        action = random.randint(0, 2)
        amount = [5, 10, 20][random.randint(0, 2)]
        sc = stock_colors[stock]
        ac = action_colors[actions[action]]
        # print(f"> {stock} {ac}{actions[action]}{r} {amount}")
        x, y = self.log_win.getmaxyx()
        self.log_win.scroll(1)
        self.log_win.hline(y+2, 0, " ", 60)
        self.log_win.addstr(y+2, 2, f"{stock}", sc)
        self.log_win.addstr(f" {actions[action]}", ac)
        self.log_win.addstr(f" {amount}")
        
        if action == DOWN:
            self.values[stock] -= amount
            if self.values[stock] <= 0:
                # print(f"{stock} bust!")
                for name, player in self.players.items():
                    player.holdings[stock] = 0
                self.values[stock] = 100
        elif action == UP:
            self.values[stock] += amount
            if self.values[stock] >= 200:
                # print(f"{stock} split!")
                for name, player in self.players.items():
                    player.holdings[stock] *= 2
                self.values[stock] = 100
        elif action == DIV:
            for name, player in self.players.items():
                player.money += amount * player.holdings[stock] // 100

    def _draw_title(self, scr, title):
        scr.addch(0, 3, curses.ACS_SBSS)
        scr.addstr(f" {title} ", curses.A_BOLD)
        scr.addch(curses.ACS_SSSB)

    def draw(self):

        # draw stocks
        self.board_win.erase()
        self.board_win.border()
        for i in range(num_stocks):
            stock = stocks[i]
            x = self.values[stock] // 5 - 1
            self.board_win.addstr(i + 1, 1, f"{stock: >10}", stock_colors[stock])
            self.board_win.addstr(i + 1, 14, f"{self.values[stock]/100:.2f}")
            self.board_win.addch(i + 1, 20 + x, "*", stock_colors[stock])
            self.board_win.vline(1, 12, curses.ACS_VLINE, num_stocks)
            self.board_win.vline(1, 19, curses.ACS_VLINE, num_stocks)
        self._draw_title(self.board_win, "market")
        self.board_win.refresh()

        # draw players
        self.holdings_win.border(0)
        for i in range(num_stocks):
            stock = stocks[i]
            attr = [curses.A_NORMAL, curses.A_UNDERLINE][i == self.current_stock]
            self.holdings_win.addstr(i + 2, 1 + 10 - len(stock), f"{stock}", stock_colors[stock] | attr)
        self.holdings_win.hline(num_stocks + 2, 1, curses.ACS_HLINE, 58)
        self.holdings_win.addstr(num_stocks + 3, 1, "cash".rjust(10), curses.color_pair(rgb(2, 5, 0)))
        self.holdings_win.addstr(num_stocks + 4, 1, "net worth".rjust(10), curses.color_pair(rgb(5, 5, 5)))
        j = 0
        for name, player in self.players.items():
            net_worth = 0
            for stock in stocks:
                net_worth += player.holdings[stock] * self.values[stock] // 100
            net_worth += player.money
            attr = curses.A_NORMAL
            if j == self.current_player:
                attr = curses.A_UNDERLINE
            j += 1
            self.holdings_win.addstr(1, 12 * j + (10 - len(name)), f"{name}", attr)
            self.holdings_win.addstr(num_stocks + 3, 12 * j, f"{player.money: >10}")
            self.holdings_win.addstr(num_stocks + 4, 12 * j, f"{net_worth: >10}")
            for i in range(num_stocks):
                stock = stocks[i]
                self.holdings_win.addstr(i + 2, 12 * j, f"{player.holdings[stock]: >10}")
        self._draw_title(self.holdings_win, "holdings")
        self.holdings_win.refresh()

        self.log_win.border(0)
        self._draw_title(self.log_win, "game log")
        self.log_win.refresh()

        self.action_win.erase()
        self.action_win.border(0)
        self._draw_title(self.action_win, "action")
        if self.current_action == ACTION_ROLL:
            self.action_win.addstr(2, 2, "Actions:", curses.A_UNDERLINE)
            self.action_win.addstr(3, 4, "r: Roll dice")
            self.action_win.addstr(4, 4, "R: Roll dice 10 times")
            self.action_win.addstr(5, 4, "b: Buy stocks")
            self.action_win.addstr(6, 4, "s: Sell stocks")
            self.action_win.addstr(7, 4, "q: Quit game")
        else:
            action = "Buy"
            if self.current_action == ACTION_SELL:
                action = "Sell"
            player = self.players_list[self.current_player]
            stock = stocks[self.current_stock]
            sc = stock_colors[stock]
            cost_per_500 = self.values[stock] * 5
            max_buy = 500 * (player.money // cost_per_500)

            if self.current_action == ACTION_SELL:
                if self.current_buy > player.holdings[stock]:
                    self.current_buy = player.holdings[stock]
            elif self.current_buy > max_buy:
                self.current_buy = max_buy

            self.current_value = self.current_buy * self.values[stock] // 100
            
            self.action_win.addstr(2, 2, f"{action}: ", curses.A_BOLD)
            self.action_win.addstr(f"{self.current_buy} ")
            self.action_win.addstr(f"{stock}", sc)
            self.action_win.addstr(f" for {self.current_value}")
            self.action_win.addstr(3, 2, "  left/right arrow keys to change amount by 500")
            self.action_win.addstr(4, 2, "  shift + left/right arrow keys to change amount by 2500")
            self.action_win.addstr(5, 2, "  backspace to finish")

        self.action_win.refresh()

        # for i in range(17):
        #     self.stdscr.addstr(0, i, "A", curses.color_pair(i))

        # for i in range(42):
        #     for j in range(6):
        #         self.stdscr.addstr(i+1, j, "A", curses.color_pair(17 + i * 6 + j))
        # self.stdscr.refresh()

        return
        print(" " * 9  + "bust                  par               split")
        print(" " * 11 +   "v                    v                  v")
        for i in range(num_stocks):
            stock = stocks[i]
            x = self.values[stock] // 5 - 1
            indicator = " " * x + "*"
            indicator = indicator.ljust(39)
            c = stock_colors[stock]
            r = Style.RESET_ALL
            print(f"{c}{stock:>10}{r} |{indicator}| {c}{self.values[stock]/100:.2f}{r}")
        
        print()
        print("  Player  |  Money  | Net Worth | Holdings")
        for name, player in players.items():
            net_worth = 0
            for stock in stocks:
                net_worth += player.holdings[stock] * self.values[stock] // 100
            net_worth += player.money
            # player.draw(net_worth)
            holdings = ", ".join([f"{amt} {stk}" for stk, amt in player.holdings.items()])
            print(f"{player.name.rjust(9)} | {player.money: >7} | {net_worth: >9} | {holdings}")

    def get_players(self):
        #initialize players
        #num_players = int(input("Number of players: "))

        # for i in range(num_players):
        #     name = input(f"Player {i+1} name?: ")
        #     self.players[name] = Player(name)

        names = ["aaron", "aaron2", "aaron3"]
        self.players = {name: Player(name) for name in names}
        self.players_list = [self.players[name] for name in names]

    def main(self):
        # game loop
        while True:
            # print game state
            self.draw()
            k = self.stdscr.getch()

            if k == ord("r"):
                self.roll()
            if k == ord("R"):
                for i in range(10): self.roll()
            if k == ord("b") and self.current_action == ACTION_ROLL:
                self.current_action = ACTION_BUY
                self.action_win.erase()
            if k == ord("s") and self.current_action == ACTION_ROLL:
                self.action_win.erase()
                self.current_action = ACTION_SELL
            if k == curses.KEY_BACKSPACE:
                if self.current_action in [ACTION_BUY, ACTION_SELL]:
                    self.action_win.erase()
                    self.action_win.refresh()
                    self.current_action = ACTION_ROLL

            if k == curses.KEY_UP:
                self.current_stock = (self.current_stock - 1) % num_stocks
            if k == curses.KEY_DOWN:
                    self.current_stock = (self.current_stock + 1) % num_stocks

            if self.current_action == ACTION_ROLL:
                if k == curses.KEY_LEFT:
                    self.current_player = (self.current_player - 1) % self.num_players
                if k == curses.KEY_RIGHT:
                    self.current_player = (self.current_player + 1) % self.num_players
            else:
                if k == curses.KEY_SLEFT:
                    self.current_buy = max(500, self.current_buy - 2500)
                elif k == curses.KEY_LEFT:
                    self.current_buy = max(500, self.current_buy - 500)
                elif k == curses.KEY_SRIGHT:
                    self.current_buy += 2500
                elif k == curses.KEY_RIGHT:
                    self.current_buy += 500
                elif k == 10:
                    print("Enter")
                    player = self.players_list[self.current_player]
                    stock = stocks[self.current_stock]
                    if self.current_action == ACTION_BUY:
                        player.money -= self.current_value
                        player.holdings[stock] += self.current_buy
                    else:
                        player.money += self.current_value
                        player.holdings[stock] -= self.current_buy
                    # self.current_buy = 0
                    # self.current_value = 0

def main(stdscr):
    global stock_colors, action_colors

    curses.use_default_colors()
    for i in range(255):
        curses.init_pair(i+1, i, -1)
    stock_colors = {
        "grain": curses.color_pair(rgb(3, 2, 0)),
        "industrial": curses.color_pair(rgb(4, 2, 2)),
        "bonds": curses.color_pair(rgb(0, 3, 1)),
        "oil": curses.color_pair(rgb(1, 1, 1)),
        "silver": curses.color_pair(rgb(4, 4, 4)),
        "gold": curses.color_pair(rgb(5, 4, 0))
    }

    action_colors = {
        "up": curses.color_pair(rgb(0, 5, 0)),
        "down": curses.color_pair(rgb(5, 0, 0)),
        "div": curses.color_pair(rgb(0, 5, 5))
    }

    stdscr.keypad(True)

    if curses.COLS < 80:
        print("Terminal must be at least 80 characters wide")
        return

    game = Game(stdscr)


src = None
if __name__ == "__main__":

    #game = Game()
    curses.wrapper(main)
    
