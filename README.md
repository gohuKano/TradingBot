A simple trading bot based on a moving average trading strategy:

Long Position: 
Enter a long position when the 9-period EMA (Exponential Moving Average) crosses above the 18-period EMA.
Set the stop-loss (SL) at the current value of the 40-period EMA at the time the long position is opened.

Short Position: 
Enter a short position when the 9-period EMA crosses below the 18-period EMA.
Set the stop-loss (SL) similarly at the current value of the 40-period EMA at the time the short position is opened.

No take-profit (TP) logic has been implemented yet.
