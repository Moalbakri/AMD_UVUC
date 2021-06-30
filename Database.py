# Libraries
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship, backref
# from Database import Base
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Date, Integer, String, Boolean, Float, BigInteger
from sqlalchemy.dialects.postgresql import TIMESTAMP
# the path of the Database, that connected with sqlite
path = 'sqlite:////home/mohal/open/Bachelorarbeit/myData2.db'
engine = create_engine(path, echo=True)
Base = declarative_base()

# identify the Processor
class machine(Base):
    __tablename__ = "machine"
    id = Column(Integer, primary_key=True)
    host_name=Column(String)
    metadata_ = Column(String)
    def __repr__(self):
        return "<machine(Host Name='%s')>" % (self.host_name)

# undervolting Information
class undervolt(Base):
    __tablename__ = "undervolt"
    id = Column(Integer, primary_key=True)
    freq = Column(Integer)
    voltage = Column(Float)
    machine_id = Column(Integer, ForeignKey('machine.id'), default=1)
    machine = relationship("machine", backref=backref("undervolt", cascade="all, delete-orphan"))

    def __repr__(self):
        return "<undervolt(Frequenz='%d', voltage='%d')>" % (self.freq, self.voltage)

# measurement values
class RaplDatum(Base):
    __tablename__ = 'rapldata'
    id = Column(Integer, primary_key=True)
    undervolt_id = Column(Integer, ForeignKey('undervolt.id'))
    undervolt = relationship("undervolt", backref=backref("rapldata", cascade="all, delete-orphan"))
    temperature = Column(Float)
    aktive_core = Column(Integer)
    core_j = Column(BigInteger, nullable=False)

    def __repr__(self):
        return "<RaplDatum(temperature='%d' ,core_uj='%d')>" % (
            self.temperature, self.core_uj)

# Benchmarking Information
class Benchmark_execution(Base):
    __tablename__ = 'Benchmark_execution'
    id = Column(Integer, primary_key=True)
    Benchmark_anz = Column(Integer, default=2)
    time_start = Column(TIMESTAMP)
    time_end = Column(TIMESTAMP)
    benchmarking = Column(Boolean, default=False)
    duration = Column(Float)
    undervolt_id = Column(Integer, ForeignKey('undervolt.id'))
    undervolt = relationship("undervolt", backref=backref("Benchmark_execution", cascade="all, delete-orphan"))

    def __repr__(self):
        return "<Benchmark_execution(Benchmarking='%r', duration='%f',Benchmark_anz='%d')>" % (
        self.benchmarking, self.duration, self.Benchmark_anz)

# Benchmarks
class Benchmarks(Base):
    __tablename__ = 'Benchmarks'
    id = Column(Integer, primary_key=True)
    bench_art = Column(String)
    execution_command = Column(String)
    Benchmark_execution_id = Column(Integer, ForeignKey('Benchmark_execution.id'))
    Benchmark_execution = relationship("Benchmark_execution",
                                       backref=backref("Benchmarks", cascade="all, delete-orphan"))
    finished = Column(Boolean, default=False)

    def __repr__(self):
        return "<Benchmarks(bench1_art='%s', execution_command='%s',Benchmark_execution_id='%d', finished='%r')>" % (
        self.bench_art, self.execution_command, self.Benchmark_execution_id, self.finished)
# create session
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session(expire_on_commit=True, autoflush=False)
