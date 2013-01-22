"""Testing for pytimecode"""

import pytimecode, time

n = 0
startTC = pytimecode.PyTimeCode('29.97', '01:00:00:00', drop_frame=True)
startTime = time.time()
while n < 5:
    tc = startTC + pytimecode.PyTimeCode('29.97', start_seconds=(time.time()-startTime))
    print(tc)
    time.sleep(.1)
    n += .1
