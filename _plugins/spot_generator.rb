require 'json'

module Jekyll
  class SpotPageGenerator < Generator
    safe true
    priority :normal

    def generate(site)
      items = load_json(site, '_rawdata/spot.json')

      Jekyll.logger.info "SpotGenerator:", "#{items.size}개 관광지 페이지 생성 중..."
      items.each do |s|
        next if s['slug'].to_s.strip.empty?
        site.pages << SpotPage.new(site, s)
      end

      Jekyll.logger.info "SpotGenerator:", "완료 (#{items.size}개)"
    end

    private

    def load_json(site, path)
      file = File.join(site.source, path)
      return [] unless File.exist?(file)
      JSON.parse(File.read(file, encoding: 'utf-8'))
    rescue => e
      Jekyll.logger.warn "SpotGenerator:", "#{path} 로드 실패: #{e.message}"
      []
    end
  end

  class SpotPage < Page
    def initialize(site, s)
      @site = site
      @base = site.source
      @dir  = "spot/#{s['slug']}"
      @name = 'index.html'

      self.process(@name)
      self.read_yaml(File.join(@base, '_layouts'), 'spot.html')
      self.data.merge!(s)
      self.data['layout']      = 'spot'
      self.data['title']       = build_title(s)
      self.data['description'] = build_desc(s)
    end

    private

    def build_title(s)
      loc = [s['doShort'], s['sigungu']].compact.join(' ')
      "#{s['spotName']} #{loc} 위치·주차 정보"
    end

    def build_desc(s)
      loc = [s['doShort'], s['sigungu']].compact.join(' ')
      intro = (s['intro'] || '').gsub(/\s+/, ' ')
      "#{loc} #{s['spotName']}(#{s['type']}). #{intro}"[0, 155]
    end
  end
end
