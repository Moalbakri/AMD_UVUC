from Database import session, RaplDatum, undervolt, Benchmark_execution, Benchmarks


def clear_freq(x):
    for i in session.query(Benchmarks).join(Benchmark_execution).join(undervolt).filter(undervolt.freq == x).all():
        session.delete(i)
    session.commit()
    for i in session.query(Benchmark_execution).join(undervolt).filter(undervolt.freq == x).all():
        session.delete(i)
    session.commit()
    for i in session.query(RaplDatum).join(undervolt).filter(undervolt.freq == x).all():
        session.delete(i)
    session.commit()
    for i in session.query(undervolt).filter(undervolt.freq == x).all():
        session.delete(i)
    session.commit()
