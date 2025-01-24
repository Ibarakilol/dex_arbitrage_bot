# DEX Arbitrage Bot

Бот по поиску арбитражных сделок между DEX и CEX биржами.

## Установка

1. Нужно установить uv, пакетный менеджер для Python (аналог npm/yarn для JS)

```
$ pip install uv
```

2. Клонирование репозитория

```
$ git clone https://github.com/Ibarakilol/dex_arbitrage_bot.git
$ cd dex_arbitrage_bot
```

3. Установка зависимостей

```
$ uv sync
```

3. Переименовать файл `.env.example` в `.env`, заполнить токен от [BotFather](https://t.me/BotFather), API ключи от бирж, указать один из ([100, 200, 300, 500, 1000, 2000, 3000, 5000, 10000]) объемов (VOLUME) для торгов в USDT и минимальную прибыль в USDT (MIN_PROFIT)

4. Запуск

```
$ uv run main.py
```

## Описание

Бот автоматически ищет разницу цен между децентрализованными (в данном случае аггрегатор) и централизованными биржами. Поиск происходит в сети [Solana](https://jup.ag/), поэтому для использования бота потребуется кошелек [Solflare](https://solflare.com/) и биржи [BingX](https://bingx.com/invite/F1RGVM/), [CoinEx](https://www.coinex.com/ru/).
