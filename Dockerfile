FROM ubuntu:20.04

# Inject Condra packages by the CI/CD Pipeline to run conda create env only once
RUN mkdir -p /opt/conda/
COPY /opt/conda /opt/conda
ENV PATH /opt/conda/bin:$PATH
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/conda/lib

COPY named_entities_service named_entities_service

# Expose port for Docker (Default always 80)
EXPOSE 80
# Start your Service on the Entrypoint
ENTRYPOINT ["python", "named_entities_service"]