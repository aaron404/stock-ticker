import curses
import curses.ascii
import random

import names

UP = 0
DOWN = 1
DIV = 2

ACTION_ROLL = 0
ACTION_BUY = 1
ACTION_SELL = 2

# random.seed(0)

def rgb(r, g, b):
    return r * 36 + g * 6 + b + 17

stocks = [
    "grain",
    "industrial",
    "tech",
    "bonds",
    "oil",
    # "silver",
    # "gold",
    "rare metals",
]
longest_stock = max([len(stock) for stock in stocks] + [10])

num_stocks = len(stocks)

values = {stock: 100 for stock in stocks}
actions = ["up", "down", "div"]

class Player:
    def __init__(self, name, money=5000, ai=False):
        self.name = name
        self.money = money
        self.holdings = {stock: 0 for stock in stocks}
        self.ai = ai
    
    def play(self, values, log_win):
        if not self.ai:
            return
        purchases = {stock: 0 for stock in stocks}
        costs     = {stock: 0 for stock in stocks}
        attempts = 0
        while attempts < 1:
            stock = stocks[random.randint(0, num_stocks - 1)]
            cost_per_500 = values[stock] * 5
            if cost_per_500 <= self.money:
                self.money -= cost_per_500
                self.holdings[stock] += 500
                purchases[stock] += 500
                costs[stock] += cost_per_500
            else:
                attempts += 1
        # log purchases
        y, x = log_win.getmaxyx()
        for stock in stocks:
            sc = stock_colors[stock]
            if purchases[stock] > 0:
                log_win.scroll(1)
                log_win.hline(y-2, 1, " ", x-2)
                log_win.addstr(y-2, 2, f"{self.name} bought {purchases[stock]} ")
                log_win.addstr(f"{stock}", sc)
                log_win.addstr(f" for {costs[stock]}")

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
        self.window_w = 50 + longest_stock + 1; w = self.window_w
        self.market_win    = curses.newwin(len(stocks) + 2, w, 0, 0)
        self.holdings_win = curses.newwin(len(stocks) + 6, w, self.market_win.getmaxyx()[0], 0)
        self.action_win   = curses.newwin(curses.LINES - num_stocks * 2 - 7 - 1, w, self.holdings_win.getmaxyx()[0] + self.market_win.getmaxyx()[0], 0)
        self.log_win      = curses.newwin(curses.LINES, curses.COLS - w, 0, w)
        self.log_win.scrollok(True)
        self.action_win.keypad(True)
        
        self.main()

    def roll(self):
        stock  = random.randint(0, num_stocks - 1)
        stock  = stocks[stock]
        action = random.randint(0, 2)
        amount = [5, 10, 20][random.randint(0, 2)]
        sc = stock_colors[stock]
        ac = action_colors[actions[action]]
        y, x = self.log_win.getmaxyx()
        self.log_win.scroll(1)
        self.log_win.hline(y-2, 1, " ", x-2)
        self.log_win.addstr(y-2, 2, f"{stock}", sc)
        self.log_win.addstr(f" {actions[action]}", ac)
        self.log_win.addstr(f" {amount}")
        
        if action == DOWN:
            self.values[stock] -= amount
            if self.values[stock] <= 0:
                self.log_win.scroll(1)
                self.log_win.hline(y-2, 1, " ", x-2)
                self.log_win.addstr(y-2, 2, f"{stock} bust!".center(x - 5), curses.color_pair(rgb(5, 0, 0)) | curses.A_STANDOUT)
                for name, player in self.players.items():
                    player.holdings[stock] = 0
                self.values[stock] = 100
        elif action == UP:
            self.values[stock] += amount
            if self.values[stock] >= 200:
                self.log_win.scroll(1)
                self.log_win.hline(y-2, 1, " ", x-2)
                self.log_win.addstr(y-2, 2, f"{stock} split!".center(x - 5), curses.color_pair(rgb(2, 5, 0)) | curses.A_STANDOUT)
                for name, player in self.players.items():
                    player.holdings[stock] *= 2
                self.values[stock] = 100
        elif action == DIV:
            if self.values[stock] >= 100:
                for name, player in self.players.items():
                    player.money += amount * player.holdings[stock] // 100

    def _draw_title(self, scr, title):
        scr.addch(0, 3, curses.ACS_SBSS)
        scr.addstr(f" {title.upper()} ", curses.A_BOLD)
        scr.addch(curses.ACS_SSSB)

    def draw(self):
        # draw stocks
        x = longest_stock + 3
        self.market_win.erase()
        self.market_win.border()
        self.market_win.vline(1,      x, curses.ACS_VLINE, num_stocks)
        self.market_win.vline(1, x +  7, curses.ACS_VLINE, num_stocks)
        self.market_win.vline(1, x + 17, curses.ACS_BULLET, num_stocks)
        self.market_win.vline(1, x + 27, curses.ACS_VLINE, num_stocks)
        self.market_win.vline(1, x + 37, curses.ACS_BULLET, num_stocks)
        for i in range(num_stocks):
            stock = stocks[i]
            v = self.values[stock] // 5 - 1
            self.market_win.addstr(i + 1, 1, f"{stock: >{longest_stock + 1}}", stock_colors[stock])
            self.market_win.addstr(i + 1, x + 2, f"{self.values[stock]/100:.2f}")
            self.market_win.addch(i + 1, x + v + 8, curses.ACS_DIAMOND, stock_colors[stock])
        self._draw_title(self.market_win, "market")
        self.market_win.refresh()

        # draw players
        self.holdings_win.border(0)
        for i in range(num_stocks):
            stock = stocks[i]
            attr = [curses.A_NORMAL, curses.A_UNDERLINE][i == self.current_stock]
            self.holdings_win.addstr(i + 2, 2 + longest_stock - len(stock), f"{stock}", stock_colors[stock] | attr)
        self.holdings_win.hline(num_stocks + 2, 1, curses.ACS_HLINE, self.window_w - 2)
        self.holdings_win.addstr(num_stocks + 3, 2, "cash".rjust(longest_stock), curses.color_pair(rgb(2, 5, 0)))
        self.holdings_win.addstr(num_stocks + 4, 2, "net worth".rjust(longest_stock), curses.color_pair(rgb(5, 5, 5)))
        j = 0
        for name, player in self.players.items():
            net_worth = 0
            for stock in stocks:
                net_worth += player.holdings[stock] * self.values[stock] // 100
            net_worth += player.money
            attr = curses.A_NORMAL
            if j == self.current_player:
                attr = curses.A_UNDERLINE
            max_name_length = 11
            offset = longest_stock + 4 + j * max_name_length
            self.holdings_win.addstr(1, offset - len(name) + max_name_length, f"{name}", attr)
            self.holdings_win.addstr(num_stocks + 3, offset, f"{player.money: >{longest_stock}}")
            self.holdings_win.addstr(num_stocks + 4, offset, f"{net_worth: >{longest_stock}}")
            for i in range(num_stocks):
                stock = stocks[i]
                self.holdings_win.addstr(i + 2, offset, f"{player.holdings[stock]: >{longest_stock}}")
            j += 1
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
            self.action_win.addch(8, 4, curses.ACS_LARROW)
            self.action_win.addstr(" Select previous player")
            self.action_win.addch(9, 4, curses.ACS_RARROW)
            self.action_win.addstr(" Select next player")
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
            self.action_win.addch(3, 4, curses.ACS_LARROW)
            self.action_win.addch(3, 5, " ")
            self.action_win.addch(3, 6, curses.ACS_RARROW)
            self.action_win.addstr(" to change amount by 500")
            self.action_win.addstr(4, 4, "shift + ")
            self.action_win.addch(curses.ACS_LARROW)
            self.action_win.addch(" ")
            self.action_win.addch(curses.ACS_RARROW)
            self.action_win.addstr(" to change amount by 2500")
            self.action_win.addstr(5, 4, f"m: max {action.lower()}")
            # self.action_win.addstr(4, 4, "  shift + left/right arrow keys to change amount by 2500")
            self.action_win.addstr(6, 4, "backspace to finish")

        self.action_win.refresh()

    def get_players(self):
        #initialize players
        #num_players = int(input("Number of players: "))

        # for i in range(num_players):
        #     name = input(f"Player {i+1} name?: ")
        #     self.players[name] = Player(name)
        player_names = ["Aaron"]
        while len(player_names) < 4:
            name = names.get_first_name()
            if not name in player_names:
                player_names.append(name)
        
        self.players = {name: Player(name, ai=name!="Aaron") for name in player_names}
        self.players_list = [self.players[name] for name in player_names]
        import json
        open("names.txt", "w").write(json.dumps(player_names))

    def play(self):
        for player in self.players_list:
            player.play(self.values, self.log_win)

    def main(self):
        self.play()
        # game loop
        while True:
            # print game state
            self.draw()
            k = self.action_win.getch()
            if k == ord("r"):
                self.roll()
            if k == ord("R"):
                for i in range(10): self.roll()
                for player in self.players_list:
                    player.play(self.values, self.log_win)
            elif k == ord("q"):
                return
            if k == ord("b"):
                self.current_action = ACTION_BUY
                self.action_win.erase()
            if k == ord("s"):
                self.action_win.erase()
                self.current_action = ACTION_SELL
            if k == curses.KEY_BACKSPACE:
                if self.current_action in [ACTION_BUY, ACTION_SELL]:
                    self.action_win.erase()
                    self.action_win.refresh()
                    self.current_action = ACTION_ROLL
            if k == ord("p"):
                self.players_list[self.current_player].play(self.values, self.log_win)
            if k == ord("P"):
                for player in self.players_list:
                    player.play(self.values, self.log_win)

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
                elif k == 10 and self.current_buy > 0:
                    player = self.players_list[self.current_player]
                    stock = stocks[self.current_stock]
                    sc = stock_colors[stock]
                    y, x = self.log_win.getmaxyx()
                    self.log_win.scroll(1)
                    self.log_win.hline(y - 2, 1, " ", x-2)
                    self.log_win.addstr(y - 2, 2, f"{stock}", sc)
                    if self.current_action == ACTION_BUY:
                        player.money -= self.current_value
                        player.holdings[stock] += self.current_buy
                        self.log_win.addstr(y - 2, 2, f"{player.name} bought {self.current_buy} ")
                    else:
                        player.money += self.current_value
                        player.holdings[stock] -= self.current_buy
                        self.log_win.addstr(y - 2, 2, f"{player.name} sold {self.current_buy} ")
                    self.log_win.addstr(f"{stock}", sc)
                    # self.log_win.addstr(y - 2, 4, f" for {self.current_value}")
                    self.log_win.addstr(f" for {self.current_value}")
                elif k == ord('m'):
                    self.current_buy = 10000000
def main(stdscr):
    global stock_colors, action_colors

    curses.use_default_colors()
    for i in range(255):
        curses.init_pair(i+1, i, -1)
    stock_colors = {
        "grain": curses.color_pair(rgb(4, 3, 1)),
        "industrial": curses.color_pair(rgb(4, 2, 2)),
        "bonds": curses.color_pair(rgb(0, 3, 1)),
        "oil": curses.color_pair(rgb(1, 1, 1)),
        "silver": curses.color_pair(rgb(4, 4, 4)),
        "gold": curses.color_pair(rgb(5, 4, 0)),
        "rare metals": curses.color_pair(rgb(5, 4, 0)),
        "tech": curses.color_pair(rgb(0, 4, 5))
    }

    action_colors = {
        "up": curses.color_pair(rgb(0, 5, 0)),
        "down": curses.color_pair(rgb(5, 0, 0)),
        "div": curses.color_pair(rgb(0, 5, 5))
    }

    #stdscr.keypad(True)
    curses.curs_set(0)

    if curses.COLS < 80:
        print("Terminal must be at least 80 characters wide")
        return

    game = Game(stdscr)


src = None
if __name__ == "__main__":

    #game = Game()
    curses.wrapper(main)
    
